from __future__ import annotations

import json
import re
from contextlib import contextmanager
from typing import Any, Iterable, Optional

import psycopg

from ..configuration import RuntimeConfig


_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_QUALIFIED = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*$")


def safe_ident(name: str) -> str:
    if not _IDENT.fullmatch(name):
        raise ValueError(f"Unsafe SQL identifier in profile: {name!r}")
    return name


def safe_table(name: str) -> str:
    if not _QUALIFIED.fullmatch(name):
        raise ValueError(f"Unsafe qualified SQL table in profile: {name!r}")
    return name


class PostgresStore:
    def __init__(self, cfg: RuntimeConfig):
        self.cfg = cfg
        self.settings = cfg.settings
        self.source = cfg.museum.metadata["source"]
        self.source_table = safe_table(str(self.source["table"]))
        self.id_col = safe_ident(str(self.source["id_column"]))

        # Canonical asset configuration.
        #
        # New profiles:
        #   asset:
        #     mode: s3 | url
        #     column: <source column>
        #
        # Legacy profiles using image_url_column/image_key remain supported
        # and are interpreted as S3-backed assets.
        asset = self.source.get("asset")
        if asset:
            self.asset_mode = str(asset.get("mode") or "").strip().lower()
            self.asset_col = safe_ident(str(asset["column"]))
            self.asset_key = asset.get("key") or {}
        else:
            self.asset_mode = "s3"
            self.asset_col = safe_ident(str(self.source["image_url_column"]))
            self.asset_key = self.source.get("image_key") or {}

        coll = self.source.get("collection_column")
        self.collection_col = safe_ident(str(coll)) if coll else None

    def connect(self) -> psycopg.Connection:
        return psycopg.connect(self.settings.pg_conninfo(), autocommit=False)

    @contextmanager
    def cursor(self, conn):
        cur = conn.cursor()
        try:
            yield cur
        finally:
            cur.close()

    def fetch_all(self, conn, sql: str, params: Optional[Iterable[Any]] = None) -> list[dict]:
        with self.cursor(conn) as cur:
            cur.execute(sql, params or ())
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def fetch_one(self, conn, sql: str, params: Optional[Iterable[Any]] = None) -> Optional[dict]:
        rows = self.fetch_all(conn, sql, params)
        return rows[0] if rows else None

    def fetch_source_row(self, conn, obj_id: str) -> Optional[dict]:
        return self.fetch_one(conn, f"SELECT * FROM {self.source_table} WHERE {self.id_col}=%s", (obj_id,))

    def _asset_ref(self, raw_value: str) -> dict[str, str]:
        value = str(raw_value or "")

        if self.asset_mode == "s3":
            marker = str(self.asset_key.get("marker", "/objects/"))
            prefix = str(self.asset_key.get("prefix", "objects/"))
            if marker and marker in value:
                value = prefix + value.split(marker, 1)[1]

        return {"mode": self.asset_mode, "value": value}

    def pick_objects(self, conn, limit: int = 20, ids: list[str] | None = None,
                     collections: list[str] | None = None) -> list[dict]:
        # Explicit IDs are returned regardless of completion; the phase runner
        # decides what is already done. This is useful for controlled tests.
        where = [f"{self.asset_col} IS NOT NULL"]
        params: list[Any] = []
        if ids:
            where.append(f"{self.id_col} = ANY(%s)")
            params.append(ids)
        if collections and self.collection_col:
            where.append(f"{self.collection_col} = ANY(%s)")
            params.append(collections)
        sql = (
            f"SELECT {self.id_col} AS obj_id, {self.asset_col} AS asset_value"
            + (f", {self.collection_col} AS collection" if self.collection_col else "")
            + f" FROM {self.source_table} WHERE " + " AND ".join(where)
            + f" ORDER BY {self.id_col}"
        )
        if not ids:
            sql += " LIMIT %s"
            params.append(limit)
        rows = self.fetch_all(conn, sql, params)
        for r in rows:
            raw_value = str(r.pop("asset_value", "") or "")
            r["asset_ref"] = self._asset_ref(raw_value)
        return rows

    def pick_open_objects(self, conn, modules: dict[str, bool], limit: int = 20,
                          collections: list[str] | None = None) -> list[dict]:
        # Keep SQL museum-schema assumptions inside the persistence adapter;
        # the harness only knows module names. We overfetch and test completion
        # so a partially processed database still yields `limit` open objects.
        candidates = self.pick_objects(conn, limit=max(limit * 20, 200), collections=collections)
        enabled = [m for m, on in modules.items() if on]
        out=[]
        for row in candidates:
            if any(not self.module_done(conn, m, row["obj_id"]) for m in enabled):
                out.append(row)
                if len(out) >= limit:
                    break
        return out

    # --- Generic context reads ---------------------------------------------
    def master_caption(self, conn, obj_id: str) -> str:
        row = self.fetch_one(conn, "SELECT master_caption FROM museum.enrichment_captions WHERE obj_id=%s ORDER BY erstellt_am DESC LIMIT 1", (obj_id,))
        return str((row or {}).get("master_caption") or "")

    def keywords(self, conn, obj_id: str, clusters: list[str]) -> str:
        if not clusters:
            return ""
        row = self.fetch_one(conn, """
            SELECT string_agg(DISTINCT keyword, ', ') AS value
            FROM museum.enrichment_keywords
            WHERE obj_id=%s AND status <> 'red' AND cluster = ANY(%s)
        """, (obj_id, clusters))
        return str((row or {}).get("value") or "")

    def query_profile_resource(self, conn, path) -> dict:
        sql = path.read_text(encoding="utf-8")
        return self.fetch_one(conn, sql) or {}


    def _text_from_profile_fields(self, row: dict, spec: dict) -> str:
        """Build a text representation from profile-defined canonical fields."""
        field_by_id = {
            str(f["id"]): f
            for f in self.cfg.museum.metadata.get("fields", [])
        }
        labels = spec.get("labels") or {}
        parts: list[str] = []

        for field_id in spec.get("include") or []:
            field_id = str(field_id)
            field = field_by_id.get(field_id)
            if field is None:
                raise RuntimeError(
                    f"text_embeddings references unknown metadata field: {field_id}"
                )

            value = row.get(str(field["source"]))
            if value is None:
                continue

            text = str(value).strip()
            if not text:
                continue

            label = str(labels.get(field_id) or "").strip()
            parts.append(f"{label}: {text}" if label else text)

        return ". ".join(parts)

    @staticmethod
    def _join_text_parts(*parts: str) -> str:
        return ". ".join(str(p).strip() for p in parts if str(p or "").strip())

    def text_embedding_row(self, conn, obj_id: str) -> dict:
        """
        Build the canonical text-embedding inputs without depending on an
        institution-specific SQL view or source schema.
        """
        cfg = self.cfg.museum.metadata.get("text_embeddings") or {}
        source_row = self.fetch_source_row(conn, obj_id) or {}

        basis = self._text_from_profile_fields(
            source_row,
            cfg.get("basis") or {},
        )
        flowing = self._text_from_profile_fields(
            source_row,
            cfg.get("flowing_text") or {},
        )

        tags = self.fetch_one(
            conn,
            """
            SELECT string_agg(DISTINCT keyword, ', ') AS value
            FROM museum.enrichment_keywords
            WHERE obj_id=%s AND COALESCE(status, '') <> 'red'
            """,
            (obj_id,),
        ) or {}
        keywords = str(tags.get("value") or "").strip()

        caption = self.fetch_one(
            conn,
            """
            SELECT text_visuell, text_kontext
            FROM museum.enrichment_captions
            WHERE obj_id=%s AND COALESCE(parse_ok, false)=true
            ORDER BY erstellt_am DESC
            LIMIT 1
            """,
            (obj_id,),
        ) or {}

        text_visuell = str(caption.get("text_visuell") or "").strip()
        text_kontext = str(caption.get("text_kontext") or "").strip()
        keywords_label = str(cfg.get("keywords_label") or "Schlagworte")

        return {
            "obj_id": obj_id,
            "text_basis": basis or None,
            "text_erschliessung": (
                self._join_text_parts(
                    basis,
                    f"{keywords_label}: {keywords}",
                )
                if keywords else None
            ),
            "text_visuell": (
                self._join_text_parts(basis, text_visuell)
                if text_visuell else None
            ),
            "text_kontext": (
                self._join_text_parts(basis, text_kontext)
                if text_kontext else None
            ),
            "text_fliesstext": flowing or None,
        }

    def delete_module_results(self, conn, obj_id: str, modules: list[str]) -> None:
        tables = {
            "image_embeddings": ["museum.embeddings"],
            "image_features": ["museum.enrichment_derived"],
            "captions": ["museum.enrichment_captions"],
            "tagging": ["museum.enrichment_keywords"],
            "emotion": ["museum.emotion_assignments", "museum.emotion_runs"],
            "topics": ["museum.topic_assignments", "museum.topic_runs"],
            "text_embeddings": ["museum.embeddings"],
        }
        with self.cursor(conn) as cur:
            for module in modules:
                for table in tables.get(module, []):
                    if table == "museum.embeddings" and module == "image_embeddings":
                        cur.execute("DELETE FROM museum.embeddings WHERE obj_id=%s AND kind='image'", (obj_id,))
                    elif table == "museum.embeddings" and module == "text_embeddings":
                        cur.execute("DELETE FROM museum.embeddings WHERE obj_id=%s AND kind LIKE %s", (obj_id, "text_%"))
                    else:
                        cur.execute(f"DELETE FROM {table} WHERE obj_id=%s", (obj_id,))

    # --- Completion checks --------------------------------------------------
    _DONE = {
        "image_embeddings": "SELECT 1 FROM museum.embeddings WHERE obj_id=%s AND kind='image' LIMIT 1",
        "image_features": "SELECT 1 FROM museum.enrichment_derived WHERE obj_id=%s LIMIT 1",
        "captions": "SELECT 1 FROM museum.enrichment_captions WHERE obj_id=%s LIMIT 1",
        "tagging": "SELECT 1 FROM museum.enrichment_keywords WHERE obj_id=%s LIMIT 1",
        "emotion": "SELECT 1 FROM museum.emotion_runs WHERE obj_id=%s LIMIT 1",
        "topics": "SELECT 1 FROM museum.topic_runs WHERE obj_id=%s LIMIT 1",
        "text_embeddings": "SELECT 1 FROM museum.embeddings WHERE obj_id=%s AND kind='text_erschliessung' LIMIT 1",
    }

    def module_done(self, conn, module: str, obj_id: str) -> bool:
        sql = self._DONE.get(module)
        if not sql:
            return False
        with self.cursor(conn) as cur:
            cur.execute(sql, (obj_id,))
            return cur.fetchone() is not None

    # --- Writes -------------------------------------------------------------
    def write_image_embeddings(self, conn, obj_id: str, siglip: list[float], dino: list[float]) -> None:
        sql = """
        INSERT INTO museum.embeddings (obj_id, kind, modell, dim, vec)
        VALUES (%s,%s,%s,%s,%s::jsonb)
        ON CONFLICT (obj_id,kind,modell) DO UPDATE SET vec=EXCLUDED.vec, erstellt_am=now()
        """
        with self.cursor(conn) as cur:
            cur.execute(sql, (obj_id, "image", "siglip2-giant", len(siglip), json.dumps(siglip)))
            cur.execute(sql, (obj_id, "image", "dinov3-vitl16", len(dino), json.dumps(dino)))

    def write_text_embedding(self, conn, obj_id: str, kind: str, vec: list[float], sparse: Optional[dict]) -> None:
        sql = """
        INSERT INTO museum.embeddings (obj_id,kind,modell,dim,vec,sparse)
        VALUES (%s,%s,'bge-m3',%s,%s::jsonb,%s::jsonb)
        ON CONFLICT (obj_id,kind,modell) DO UPDATE SET
          vec=EXCLUDED.vec,sparse=EXCLUDED.sparse,dim=EXCLUDED.dim,erstellt_am=now()
        """
        with self.cursor(conn) as cur:
            cur.execute(sql, (obj_id, kind, len(vec), json.dumps(vec), json.dumps(sparse) if sparse else None))

    def write_derived(self, conn, d: dict) -> None:
        sql = """
        INSERT INTO museum.enrichment_derived
          (obj_id,format,farbigkeit,farben,chroma_mittel,hue_streuung,helligkeit_mittel)
        VALUES (%s,%s,%s,%s::jsonb,%s,%s,%s)
        ON CONFLICT (obj_id) DO UPDATE SET
          format=EXCLUDED.format,farbigkeit=EXCLUDED.farbigkeit,farben=EXCLUDED.farben,
          chroma_mittel=EXCLUDED.chroma_mittel,hue_streuung=EXCLUDED.hue_streuung,
          helligkeit_mittel=EXCLUDED.helligkeit_mittel,erstellt_am=now()
        """
        with self.cursor(conn) as cur:
            cur.execute(sql, (d["obj_id"], d["format"], d["farbigkeit"], d["farben"], d["chroma_mittel"], d["hue_streuung"], d["helligkeit_mittel"]))

    def write_captions(self, conn, c: dict) -> None:
        sql = """
        INSERT INTO museum.enrichment_captions (
          obj_id,caption,modell,version,status,master_caption,res_qwen,res_gemma,text_visuell,text_kontext,
          transkription,hat_transkription,sensitiv_flag,parse_ok,tokens_total
        ) VALUES (%s,%s,%s,%s,'vorschlag',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (obj_id,modell) DO UPDATE SET
          caption=EXCLUDED.caption,master_caption=EXCLUDED.master_caption,res_qwen=EXCLUDED.res_qwen,res_gemma=EXCLUDED.res_gemma,
          text_visuell=EXCLUDED.text_visuell,text_kontext=EXCLUDED.text_kontext,
          transkription=EXCLUDED.transkription,hat_transkription=EXCLUDED.hat_transkription,
          sensitiv_flag=EXCLUDED.sensitiv_flag,parse_ok=EXCLUDED.parse_ok,tokens_total=EXCLUDED.tokens_total,
          erstellt_am=now()
        """
        with self.cursor(conn) as cur:
            cur.execute(sql, (
                c["obj_id"], c["master_caption"], c["modell"], c["version"],
                c["master_caption"], c["res_qwen"], c["res_gemma"],
                c["text_visuell"], c["text_kontext"], c["transkription"],
                c["hat_transkription"], c["sensitiv_flag"], c["parse_ok"],
                c["tokens_total"],
            ))

    def write_keyword(self, conn, row: dict) -> None:
        sql = """
        INSERT INTO museum.enrichment_keywords
          (obj_id,cluster,keyword,gnd_name,gnd_id,confidence,status,llm2,llm3,llm4,hinweis,
           audit1,audit2,audit3,audit4,audit5,status2,modell)
        VALUES (%s,%s,%s,NULLIF(%s,''),NULLIF(%s,''),NULLIF(%s,''),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        with self.cursor(conn) as cur:
            cur.execute(sql, (row["obj_id"],row["cluster"],row["keyword"],row.get("gnd_name") or "",row.get("gnd_id") or "",row.get("confidence") or "",row["status"],row.get("llm2"),row.get("llm3"),row.get("llm4"),row.get("hinweis") or "",row.get("audit1") or "",row.get("audit2") or "",row.get("audit3") or "",row.get("audit4") or "",row.get("audit5") or "",row.get("status2") or "Unknown",row.get("modell") or ""))

    def write_emotion(self, conn, r: dict) -> None:
        sql = """
        INSERT INTO museum.emotion_assignments
          (obj_id,annotation_set_id,concept_id,concept_id_original,reading_statement,reading_scope,why,evidence,
           judge_status,judge_action,judge_comment,validation_issues,caption_used,perspective_type,vocabulary_version,
           generator_model,judge_model,generator_prompt,judge_prompt)
        VALUES (%s,%s,%s,NULLIF(%s,''),%s,%s,%s,%s::jsonb,%s,%s,%s,%s::text[],%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (annotation_set_id,obj_id,concept_id,reading_scope) DO NOTHING
        """
        with self.cursor(conn) as cur:
            cur.execute(sql, (r["obj_id"],r["annotation_set_id"],r["concept_id"],r.get("concept_id_original") or "",r["reading_statement"],r["reading_scope"],r["why"],r["evidence_json"],r["judge_status"],r["judge_action"],r["judge_comment"],r["validation_issues"],r["caption_used"],r["perspective_type"],r["vocabulary_version"],r["generator_model"],r["judge_model"],r["generator_prompt"],r["judge_prompt"]))

    def write_emotion_run(self, conn, r: dict) -> None:
        sql = """
        INSERT INTO museum.emotion_runs
          (obj_id,annotation_set_id,reading_count,visible_findings,depicted_situations,free_effects,unmappable_effects,
           considered_rejected,no_reading_reason,caption_used,vocabulary_version,generator_model,judge_model,generator_prompt)
        VALUES (%s,%s,%s,%s::text[],%s::text[],%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (annotation_set_id,obj_id) DO NOTHING
        """
        with self.cursor(conn) as cur:
            cur.execute(sql, (r["obj_id"],r["annotation_set_id"],r["reading_count"],r["visible_findings"],r["depicted_situations"],r["free_effects_json"],r["unmappable_effects_json"],r["considered_rejected_json"],r.get("no_reading_reason"),r["caption_used"],r["vocabulary_version"],r["generator_model"],r["judge_model"],r["generator_prompt"]))

    def write_topic(self, conn, r: dict) -> None:
        sql = """
        INSERT INTO museum.topic_assignments
          (obj_id,topic,slug,source,status,relation_types,rationale,judge_status,judge_decision,
           review_class,mandatory_review,detail,taxonomy_version,annotation_set)
        VALUES (%s,%s,%s,%s,%s,%s::text[],%s,%s,%s,%s,%s::boolean,%s::jsonb,%s,%s)
        ON CONFLICT (obj_id,topic,source) DO UPDATE SET
          status=EXCLUDED.status,relation_types=EXCLUDED.relation_types,rationale=EXCLUDED.rationale,
          judge_status=EXCLUDED.judge_status,judge_decision=EXCLUDED.judge_decision,
          review_class=EXCLUDED.review_class,mandatory_review=EXCLUDED.mandatory_review,
          detail=EXCLUDED.detail,taxonomy_version=EXCLUDED.taxonomy_version,updated_at=now()
        """
        with self.cursor(conn) as cur:
            cur.execute(sql, (r["obj_id"],r["topic"],r["slug"],r["source"],r["status"],r["relation_types"],r["rationale"],r["judge_status"],r["judge_decision"],r["review_class"],r["mandatory_review"],r["detail_json"],r["taxonomy_version"],r["annotation_set"]))

    def write_topic_run(self, conn, r: dict) -> None:
        sql = """
        INSERT INTO museum.topic_runs
          (obj_id,annotation_set_id,object_findings,taxonomy_version,generator_model,judge_model,assignment_count)
        VALUES (%s,%s,%s::jsonb,%s,%s,%s,(SELECT COUNT(*) FROM museum.topic_assignments WHERE obj_id=%s))
        ON CONFLICT (annotation_set_id,obj_id) DO UPDATE SET
          assignment_count=(SELECT COUNT(*) FROM museum.topic_assignments WHERE obj_id=EXCLUDED.obj_id)
        """
        with self.cursor(conn) as cur:
            cur.execute(sql, (r["obj_id"],r["annotation_set"],r["object_findings_json"],r["taxonomy_version"],r["generator_model"],r["judge_model"],r["obj_id"]))

    @staticmethod
    def pg_text_array(values: Optional[Iterable[Any]]) -> str:
        if not values:
            return "{}"
        cleaned=[]
        for x in values:
            s=str(x)
            for ch in '{} ,"':
                if ch != ' ':
                    s=s.replace(ch,"")
            cleaned.append(s)
        return "{"+",".join(cleaned)+"}"
