#!/usr/bin/env python3

import gzip
import json
import os
import re
import sys
import time

import ijson
import requests


GND_NS = "https://d-nb.info/standards/elementset/gnd#"

INPUT_FILE = os.environ.get(
    "GND_INPUT_FILE",
    "authorities-gnd-sachbegriff_lds.jsonld.gz",
)

OS_INDEX = os.environ.get("OS_INDEX", "gnd_sachbegriffe")
OS_TIMEOUT = int(os.environ.get("OS_TIMEOUT", "30"))
BATCH_SIZE = int(os.environ.get("GND_BATCH_SIZE", "1000"))

# Bestehende Pipeline-Konfiguration verwenden:
# OS_MSEARCH=http://.../_msearch
msearch = os.environ.get(
    "OS_MSEARCH",
    "http://127.0.0.1:9200/_msearch",
)
OS_BASE = os.environ.get(
    "OS_BASE",
    msearch.rsplit("/_msearch", 1)[0],
).rstrip("/")

CANONICAL_GND = re.compile(r"^https://d-nb\.info/gnd/([^/]+)$")


def canonical_gnd_id(uri):
    if not isinstance(uri, str):
        return None
    m = CANONICAL_GND.match(uri)
    return m.group(1) if m else None


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def literal_values(item, prop):
    out = []

    for value in as_list(item.get(GND_NS + prop)):
        if isinstance(value, dict):
            text = value.get("@value")
            if text:
                out.append(str(text).strip())
        elif isinstance(value, str):
            if not value.startswith(("http://", "https://", "_:")):
                out.append(value.strip())

    return [x for x in out if x]


def reference_ids(item, *props):
    out = []

    for prop in props:
        for value in as_list(item.get(GND_NS + prop)):
            if not isinstance(value, dict):
                continue

            gid = canonical_gnd_id(value.get("@id"))
            if gid:
                out.append(gid)

    # Reihenfolge erhalten, Duplikate entfernen
    return list(dict.fromkeys(out))


def text_field():
    return {
        "type": "text",
        "fields": {
            "keyword": {
                "type": "keyword",
                "ignore_above": 256,
            }
        },
    }


def os_request(method, path, **kwargs):
    url = f"{OS_BASE}{path}"

    response = requests.request(
        method,
        url,
        timeout=OS_TIMEOUT,
        **kwargs,
    )

    if response.status_code >= 300:
        raise RuntimeError(
            f"{method} {url} -> "
            f"{response.status_code}: {response.text[:1000]}"
        )

    return response


def create_index():
    # Leeren/alten Testindex entfernen
    r = requests.delete(
        f"{OS_BASE}/{OS_INDEX}",
        timeout=OS_TIMEOUT,
    )

    if r.status_code not in (200, 404):
        raise RuntimeError(
            f"Index konnte nicht gelöscht werden: "
            f"{r.status_code} {r.text[:500]}"
        )

    body = {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "refresh_interval": "-1",
            }
        },
        "mappings": {
            "properties": {
                "gnd_id": text_field(),
                "preferred_name": text_field(),
                "alternate_names": text_field(),
                "broader_term": text_field(),
                "related_term": text_field(),
                "def": text_field(),
            }
        },
    }

    os_request(
        "PUT",
        f"/{OS_INDEX}",
        json=body,
    )

    print(f"✓ Index '{OS_INDEX}' angelegt")


def build_name_lookup():
    """
    Pass 1:
    Alle echten Sachbegriffsressourcen erfassen.

    Wir filtern NICHT auf @type == SubjectHeading.
    Der dedizierte Sachbegriffe-Dump enthält Unterklassen.
    Entscheidendes Merkmal ist:
    preferredNameForTheSubjectHeading
    """
    names = {}

    print("Pass 1/2: GND-ID → bevorzugter Name")

    start = time.time()

    with gzip.open(INPUT_FILE, "rb") as f:
        for item in ijson.items(f, "item.item"):
            gid = canonical_gnd_id(item.get("@id"))
            if not gid:
                # Blank nodes und /about-Ressourcen
                continue

            preferred = literal_values(
                item,
                "preferredNameForTheSubjectHeading",
            )

            if not preferred:
                continue

            names[gid] = preferred[0]

            if len(names) % 25000 == 0:
                print(f"  {len(names):,} Sachbegriffe gefunden")

    elapsed = time.time() - start

    print(
        f"✓ {len(names):,} Sachbegriffe gefunden "
        f"({elapsed:.1f}s)"
    )

    if not names:
        raise RuntimeError(
            "0 Sachbegriffe gefunden – Dumpformat/Parser prüfen."
        )

    return names


def resolve_names(ids, lookup):
    return [
        lookup[gid]
        for gid in ids
        if gid in lookup
    ]


def send_bulk(lines):
    if not lines:
        return 0

    payload = (
        "\n".join(
            json.dumps(x, ensure_ascii=False)
            for x in lines
        )
        + "\n"
    )

    response = os_request(
        "POST",
        "/_bulk",
        headers={
            "Content-Type": "application/x-ndjson",
        },
        data=payload.encode("utf-8"),
    )

    result = response.json()

    if result.get("errors"):
        errors = []

        for item in result.get("items", []):
            op = item.get("index", {})

            if int(op.get("status", 500)) >= 300:
                errors.append(op)

        raise RuntimeError(
            "Bulk-Import enthält Fehler: "
            + json.dumps(
                errors[:5],
                ensure_ascii=False,
            )
        )

    return len(lines) // 2


def import_documents(name_lookup):
    print("Pass 2/2: Dokumente für OpenSearch erzeugen")

    imported = 0
    bulk = []
    start = time.time()

    broader_properties = (
        "broaderTermGeneral",
        "broaderTermGeneric",
        "broaderTermInstantial",
        "broaderTermPartitive",
        "broaderTermWithMoreThanOneElement",
    )

    related_properties = (
        "relatedTerm",
        "relatedSubjectHeading",
    )

    with gzip.open(INPUT_FILE, "rb") as f:
        for item in ijson.items(f, "item.item"):
            gid = canonical_gnd_id(item.get("@id"))

            if not gid or gid not in name_lookup:
                continue

            preferred_name = name_lookup[gid]

            alternate_names = literal_values(
                item,
                "variantNameForTheSubjectHeading",
            )

            broader_ids = reference_ids(
                item,
                *broader_properties,
            )

            related_ids = reference_ids(
                item,
                *related_properties,
            )

            broader_names = resolve_names(
                broader_ids,
                name_lookup,
            )

            related_names = resolve_names(
                related_ids,
                name_lookup,
            )

            definitions = literal_values(
                item,
                "definition",
            )

            doc = {
                "gnd_id": gid,
                "preferred_name": preferred_name,
                "alternate_names": alternate_names,
                "broader_term": broader_names,
                "related_term": related_names,
                "def": " | ".join(definitions)
                if definitions
                else "",
            }

            bulk.append({
                "index": {
                    "_index": OS_INDEX,
                    "_id": gid,
                }
            })

            bulk.append(doc)

            if len(bulk) >= BATCH_SIZE * 2:
                imported += send_bulk(bulk)
                bulk = []

                if imported % 25000 == 0:
                    print(f"  {imported:,} importiert")

    imported += send_bulk(bulk)

    os_request(
        "PUT",
        f"/{OS_INDEX}/_settings",
        json={
            "index": {
                "refresh_interval": "1s",
            }
        },
    )

    os_request(
        "POST",
        f"/{OS_INDEX}/_refresh",
    )

    elapsed = time.time() - start

    print(
        f"✓ {imported:,} Dokumente importiert "
        f"({elapsed:.1f}s)"
    )

    return imported


def verify(expected):
    response = os_request(
        "GET",
        f"/{OS_INDEX}/_count",
    )

    actual = int(response.json()["count"])

    print()
    print("=== Ergebnis ===")
    print(f"Im Dump erkannt: {expected:,}")
    print(f"Im Index:        {actual:,}")

    if actual == 0:
        raise RuntimeError(
            "Import fehlgeschlagen: Index enthält 0 Dokumente."
        )

    if actual != expected:
        raise RuntimeError(
            f"Import unvollständig: "
            f"{actual:,} von {expected:,} Dokumenten."
        )

    print("✓ GND-Sachbegriffe vollständig importiert")


def main():
    print("=== GND-Sachbegriffe → OpenSearch ===")
    print(f"Quelle: {INPUT_FILE}")
    print(f"OpenSearch: {OS_BASE}")
    print(f"Index: {OS_INDEX}")
    print()

    if not os.path.isfile(INPUT_FILE):
        raise FileNotFoundError(INPUT_FILE)

    # OpenSearch erreichbar?
    os_request("GET", "/")

    names = build_name_lookup()

    create_index()

    imported = import_documents(names)

    if imported != len(names):
        raise RuntimeError(
            f"Importer erzeugte {imported:,} statt "
            f"{len(names):,} Dokumenten."
        )

    verify(len(names))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print()
        print(f"✗ GND-Import fehlgeschlagen: {exc}")
        sys.exit(1)
