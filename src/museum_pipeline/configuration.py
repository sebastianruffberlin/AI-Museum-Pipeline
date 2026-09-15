from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .settings import Settings


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@dataclass
class MuseumProfile:
    root: Path
    data: dict[str, Any]
    metadata: dict[str, Any]
    tagging: dict[str, Any]
    tagging_policy: dict[str, Any]
    emotion: dict[str, Any]
    topics: dict[str, Any]
    authority: dict[str, Any]

    @classmethod
    def load(cls, settings: Settings) -> "MuseumProfile":
        root = settings.home / "profiles" / settings.museum_profile
        data = _load_yaml(root / "profile.yaml")
        metadata = _load_yaml(root / data["metadata"])
        tagging = _load_yaml(root / data["tagging"]["config"])
        tagging_policy = _load_yaml(root / data["tagging"]["policy"])
        emotion_cfg = (data.get("emotion") or {}).get("config")
        topics_cfg = (data.get("topics") or {}).get("config")
        authority_cfg = (data.get("authority") or {}).get("config")
        emotion = _load_yaml(root / emotion_cfg) if emotion_cfg else {}
        topics = _load_yaml(root / topics_cfg) if topics_cfg else {}
        authority = _load_yaml(root / authority_cfg) if authority_cfg else {"enabled": False}
        return cls(root, data, metadata, tagging, tagging_policy, emotion, topics, authority)

    @property
    def prompts_dir(self) -> Path:
        return self.root / self.data.get("prompts_dir", "prompts")

    def prompt(self, name: str) -> str:
        path = self.prompts_dir / f"{name}.txt"
        return path.read_text(encoding="utf-8")

    def profile_json(self, rel: str) -> Any:
        return json.loads((self.root / rel).read_text(encoding="utf-8"))


@dataclass
class ModelRegistry:
    data: dict[str, Any]
    backend: str

    @classmethod
    def load(cls, settings: Settings) -> "ModelRegistry":
        return cls(_load_yaml(settings.home / "models" / f"{settings.model_profile}.yaml"), settings.llm_backend)

    def role(self, role: str) -> dict[str, Any]:
        try:
            return self.data["roles"][role]
        except KeyError as e:
            raise KeyError(f"Unknown model role: {role}") from e

    def logical_model(self, role: str) -> str:
        return str(self.role(role)["model"])

    def api_model(self, role: str) -> str:
        cfg = self.role(role)
        name = str(cfg["model"])
        if self.backend == "cpu":
            return name + str(cfg.get("cpu_suffix", "-off"))
        return name

    def request_defaults(self, role: str) -> dict[str, Any]:
        cfg = self.role(role)
        out: dict[str, Any] = {"model": self.api_model(role)}
        out.update(cfg.get("generation") or {})
        reasoning = cfg.get("reasoning") or {"type": "none"}
        typ = reasoning.get("type", "none")
        if typ == "qwen_budget":
            out["reasoning_budget"] = int(reasoning.get("budget", 512))
        elif typ in ("qwen_thinking", "gemma_thinking"):
            out["chat_template_kwargs"] = {"enable_thinking": bool(reasoning.get("enabled", False))}
        return out

    @property
    def provenance(self) -> dict[str, Any]:
        return self.data.get("provenance") or {}


@dataclass
class HardwareProfile:
    data: dict[str, Any]

    @classmethod
    def load(cls, settings: Settings) -> "HardwareProfile":
        return cls(_load_yaml(settings.home / "hardware" / f"{settings.hardware_profile}.yaml"))

    def parallel_slots(self, model: str) -> int:
        return int((self.data.get("models") or {}).get(model, {}).get("parallel_slots", 1))

    def workers_for_role(self, models: ModelRegistry, role: str, cap: int | None = None) -> int:
        n = self.parallel_slots(models.logical_model(role))
        return max(1, min(n, cap)) if cap else max(1, n)

    def validate(self) -> list[str]:
        errors: list[str] = []
        for model, cfg in (self.data.get("models") or {}).items():
            np = int(cfg.get("parallel_slots", 1))
            pool = int(cfg.get("context_pool", 0))
            min_slot = int(cfg.get("min_context_per_slot", 0))
            if np < 1:
                errors.append(f"{model}: parallel_slots must be >= 1")
            if pool and min_slot and pool < np * min_slot:
                errors.append(
                    f"{model}: context_pool={pool} < parallel_slots({np}) * min_context_per_slot({min_slot})"
                )
        return errors

    def validate_models(self, models: ModelRegistry) -> list[str]:
        configured = set((self.data.get("models") or {}).keys())
        required = {models.logical_model(role) for role in (models.data.get("roles") or {})}
        return [f"hardware profile has no runtime entry for model: {m}" for m in sorted(required-configured)]

    def phase_workers(self, phase: str, models: ModelRegistry, role: str | None = None, cap: int | None = None) -> int:
        override = (self.data.get("phase_overrides") or {}).get(phase) or {}
        if override.get("outer_workers") is not None:
            n = int(override["outer_workers"])
        elif role:
            n = self.workers_for_role(models, role)
        else:
            kind = str(override.get("kind") or "")
            if kind == "cpu":
                n = int(self.data.get("cpu_workers", self.data.get("default_workers", 8)))
            elif kind == "service":
                n = int(self.data.get("service_workers", self.data.get("default_workers", 8)))
            else:
                n = int(self.data.get("default_workers", 8))
        return max(1, min(n, cap)) if cap else max(1, n)

    @property
    def default_workers(self) -> int:
        return int(self.data.get("default_workers", 8))


@dataclass
class WorkflowConfig:
    data: dict[str, Any]

    @classmethod
    def load(cls, settings: Settings, name: str | None = None) -> "WorkflowConfig":
        wf = name or settings.workflow
        return cls(_load_yaml(settings.home / "workflows" / f"{wf}.yaml"))

    def enabled(self, module: str) -> bool:
        return bool((self.data.get("modules") or {}).get(module, False))

    @property
    def modules(self) -> dict[str, bool]:
        return {str(k): bool(v) for k, v in (self.data.get("modules") or {}).items()}


@dataclass
class RuntimeConfig:
    settings: Settings
    museum: MuseumProfile
    models: ModelRegistry
    hardware: HardwareProfile
    workflow: WorkflowConfig

    @classmethod
    def load(cls, settings: Settings, workflow: str | None = None) -> "RuntimeConfig":
        cfg = cls(
            settings=settings,
            museum=MuseumProfile.load(settings),
            models=ModelRegistry.load(settings),
            hardware=HardwareProfile.load(settings),
            workflow=WorkflowConfig.load(settings, workflow),
        )
        errors = cfg.hardware.validate()
        errors.extend(cfg.hardware.validate_models(cfg.models))
        enabled = cfg.workflow.modules

        # Asset infrastructure is conditional on the museum profile.
        # Canonical URL assets require no presign service. S3 assets do.
        source = cfg.museum.metadata.get("source") or {}
        asset = source.get("asset") or {}
        asset_mode = str(asset.get("mode") or "").lower()

        # Legacy image_url_column/image_key profiles are interpreted as S3
        # for backwards compatibility with older reference profiles.
        if not asset_mode and source.get("image_url_column"):
            asset_mode = "s3"

        if asset_mode == "s3" and not cfg.settings.presign_url:
            errors.append("asset mode 's3' requires PRESIGN_URL")

        # Asset source validation supports S3-backed assets and direct
        # HTTP(S) image URLs. Legacy image_url_column profiles remain valid.
        source = cfg.museum.metadata.get("source") or {}
        asset = source.get("asset")
        if asset is not None:
            if not isinstance(asset, dict):
                errors.append("museum profile source.asset must be a mapping")
            else:
                mode = str(asset.get("mode") or "").strip().lower()
                if mode not in ("s3", "url"):
                    errors.append("museum profile source.asset.mode must be 's3' or 'url'")
                if not asset.get("column"):
                    errors.append("museum profile source.asset.column is required")
        elif not source.get("image_url_column"):
            errors.append(
                "museum profile source requires asset configuration "
                "(or legacy image_url_column)"
            )
        for optional in ("emotion", "topics"):
            if enabled.get(optional) and (not enabled.get("captions") or not enabled.get("tagging")):
                errors.append(f"workflow module {optional!r} requires captions + tagging")
            if enabled.get(optional) and not getattr(cfg.museum, optional):
                errors.append(f"workflow module {optional!r} is enabled but the museum profile has no {optional} configuration")
        if enabled.get("text_embeddings") and not enabled.get("captions"):
            errors.append("workflow module 'text_embeddings' requires captions")
        if enabled.get("text_embeddings") and not cfg.museum.metadata.get("text_embeddings"):
            errors.append(
                "workflow module 'text_embeddings' requires "
                "metadata.text_embeddings configuration"
            )
        if errors:
            raise RuntimeError("Invalid runtime configuration:\n- " + "\n- ".join(errors))
        return cfg
