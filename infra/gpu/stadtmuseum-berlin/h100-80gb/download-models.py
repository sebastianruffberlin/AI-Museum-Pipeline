#!/usr/bin/env python3

"""
Download the six physical LLM/VLM model sets used by the verified
Stadtmuseum H100 reference deployment.

Default policy is ROLLING:
  - fixed Unsloth repository
  - fixed quantization
  - fixed file name
  - Hugging Face revision "main"

The reference SHA256 values are provenance, not a mandatory equality
condition for rolling downloads.

This helper only downloads model files. It does not install Docker,
configure the GPU, start containers or tune concurrency.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "model-sources.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    part = Path(str(target) + ".part")

    cmd = [
        "curl",
        "-fL",
        "--retry", "5",
        "--retry-delay", "2",
        "--retry-all-errors",
    ]

    if part.exists():
        cmd += ["--continue-at", "-"]

    cmd += ["-o", str(part), url]

    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)
    os.replace(part, target)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--models-dir",
        default=os.environ.get("MODELS_DIR", "/mnt/models"),
    )
    ap.add_argument(
        "--only",
        action="append",
        default=[],
        help="local alias; may be repeated",
    )
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--check-reference",
        action="store_true",
        help="fail if downloaded bytes do not equal 2026-09-13 reference",
    )
    args = ap.parse_args()

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    models = data["models"]

    if args.only:
        wanted = set(args.only)
        models = [m for m in models if m["local_alias"] in wanted]
        missing = wanted - {m["local_alias"] for m in models}
        if missing:
            print("unknown alias:", ", ".join(sorted(missing)))
            return 2

    root = Path(args.models_dir).resolve()
    provenance = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "policy": "rolling-main",
        "models_dir": str(root),
        "files": [],
    }

    failed_reference = False

    for m in models:
        repo = m["hf_repository"]
        target_dir = root / m["local_dir"]

        jobs = [
            (
                "model",
                m["model_file"],
                target_dir / "model.gguf",
                m["reference_model_bytes"],
                m["reference_model_sha256"],
            ),
            (
                "mmproj",
                m["mmproj_file"],
                target_dir / "mmproj.gguf",
                m["reference_mmproj_bytes"],
                m["reference_mmproj_sha256"],
            ),
        ]

        print()
        print("=" * 78)
        print(m["local_alias"])
        print("repo :", repo)
        print("quant:", m["quantization"])
        print("=" * 78)

        for kind, source_file, target, ref_bytes, ref_hash in jobs:
            url = (
                f"https://huggingface.co/{repo}/resolve/main/"
                f"{source_file}"
            )

            if args.dry_run:
                print(f"{kind}: {url}")
                print(f"   -> {target}")
                continue

            if args.force or not target.is_file():
                download(url, target)
            else:
                print("exists:", target)

            actual_bytes = target.stat().st_size
            actual_hash = sha256(target)
            matches_reference = (
                actual_bytes == ref_bytes
                and actual_hash == ref_hash
            )

            provenance["files"].append(
                {
                    "alias": m["local_alias"],
                    "kind": kind,
                    "source_repository": repo,
                    "source_file": source_file,
                    "source_url": url,
                    "quantization": m["quantization"],
                    "local_path": str(target),
                    "bytes": actual_bytes,
                    "sha256": actual_hash,
                    "reference_bytes": ref_bytes,
                    "reference_sha256": ref_hash,
                    "matches_2026_09_13_reference": matches_reference,
                }
            )

            print("bytes :", actual_bytes)
            print("sha256:", actual_hash)
            print(
                "reference:",
                "MATCH" if matches_reference else "DIFF (allowed in rolling mode)",
            )

            if args.check_reference and not matches_reference:
                failed_reference = True

    if args.dry_run:
        return 0

    provenance_path = root / ".museum-pipeline-model-provenance.json"
    provenance_path.write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print()
    print("provenance:", provenance_path)

    if failed_reference:
        print("REFERENCE CHECK: FAIL")
        return 1

    print("DOWNLOAD/PROVENANCE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
