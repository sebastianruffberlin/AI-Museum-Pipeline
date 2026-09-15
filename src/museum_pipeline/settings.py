from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _req(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _opt(name: str, default: str) -> str:
    return os.environ.get(name, default).strip() or default


@dataclass(frozen=True)
class Settings:
    home: Path
    museum_profile: str
    model_profile: str
    hardware_profile: str
    workflow: str
    run_schema: str

    pg_host: str
    pg_port: str
    pg_db: str
    pg_user: str
    pg_password: str

    lcpp_url: str
    lcpp_auth: str
    lcpp_timeout: int
    lcpp_connect_timeout: int
    lcpp_max_retries: int
    llm_backend: str

    embed_base: str
    presign_url: str
    embed_timeout: int
    presign_timeout: int
    presign_expires: int

    os_msearch: str
    os_index: str
    os_timeout: int
    prompt_variant: str

    @classmethod
    def from_env(cls, home: str | Path | None = None) -> "Settings":
        default_home = Path(__file__).resolve().parents[2]
        root = Path(home or _opt("MUSEUM_PIPELINE_HOME", str(default_home))).resolve()
        backend = _opt("LLM_BACKEND", "gpu").lower()
        timeout_default = "6000" if backend == "cpu" else "600"
        embed_base = _opt("EMBED_BASE", "https://embed.example.org")
        return cls(
            home=root,
            museum_profile=_req("MUSEUM_PROFILE"),
            model_profile=_opt("MODEL_PROFILE", "reference"),
            hardware_profile=_opt("HARDWARE_PROFILE", "h100-80gb"),
            workflow=_opt("WORKFLOW", "core"),
            run_schema=_opt("MUSEUM_RUN_SCHEMA", "pipeline_runtime"),
            pg_host=_req("PG_HOST"), pg_port=_opt("PG_PORT", "5432"),
            pg_db=_req("PG_DB"), pg_user=_req("PG_USER"), pg_password=_req("PG_PASSWORD"),
            lcpp_url=_opt("LCPP_URL", "https://lcpp-gpu.example.org/v1/chat/completions"),
            lcpp_auth=_req("LCPP_AUTH"), lcpp_timeout=int(_opt("LCPP_TIMEOUT", timeout_default)),
            lcpp_connect_timeout=int(_opt("LCPP_CONNECT_TIMEOUT", "12")),
            lcpp_max_retries=int(_opt("LCPP_MAX_RETRIES", "4")), llm_backend=backend,
            embed_base=embed_base.rstrip("/"),
            presign_url=_opt("PRESIGN_URL", ""),
            embed_timeout=int(_opt("EMBED_TIMEOUT", "300")),
            presign_timeout=int(_opt("PRESIGN_TIMEOUT", "30")),
            presign_expires=int(_opt("PRESIGN_EXPIRES", "3600")),
            os_msearch=_opt("OS_MSEARCH", "http://gnd_opensearch:9200/_msearch"),
            os_index=_opt("OS_INDEX", "gnd_sachbegriffe"),
            os_timeout=int(_opt("OS_TIMEOUT", "30")),
            prompt_variant=_opt("PROMPT_VARIANT", "reference"),
        )

    def pg_conninfo(self) -> str:
        return (
            f"host={self.pg_host} port={self.pg_port} dbname={self.pg_db} "
            f"user={self.pg_user} password={self.pg_password}"
        )

    @property
    def embed_image_url(self) -> str:
        return f"{self.embed_base}/embed/image"

    @property
    def embed_text_url(self) -> str:
        return f"{self.embed_base}/embed/text"
