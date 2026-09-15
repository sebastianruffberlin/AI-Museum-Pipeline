#!/usr/bin/env python3

import argparse
import csv
import hashlib
from pathlib import Path


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "model-manifest.tsv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("models_dir")
    ap.add_argument(
        "--sha256",
        action="store_true",
        help="also read all model bytes and compare reference SHA256",
    )
    args = ap.parse_args()

    root = Path(args.models_dir).resolve()

    with MANIFEST.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    failed = False

    print("H100 REFERENCE MODEL CHECK")
    print("=" * 88)

    for row in rows:
        rel = row["path"]
        expected_bytes = int(row["bytes"])
        expected_hash = row["sha256"]
        p = root / rel

        if not p.is_file():
            print("MISS ", rel)
            failed = True
            continue

        actual_bytes = p.stat().st_size

        if actual_bytes != expected_bytes:
            print(
                f"SIZE  {rel}: actual={actual_bytes} "
                f"reference={expected_bytes}"
            )
            failed = True
            continue

        if args.sha256:
            actual_hash = sha256(p)
            if actual_hash != expected_hash:
                print(
                    f"HASH  {rel}: actual={actual_hash} "
                    f"reference={expected_hash}"
                )
                failed = True
                continue

        print("OK   ", rel)

    print("=" * 88)

    if failed:
        print("REFERENCE MODEL CHECK: FAIL")
        return 1

    print("REFERENCE MODEL CHECK: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
