from __future__ import annotations

import argparse
from pathlib import Path
import os
import shutil
import sys

from .config import (
    InstallerConfigError,
    build_runtime_env,
    load_deployment,
    load_env,
    merge_generated_secrets,
    write_env,
)
from .doctor import print_doctor, run_doctor
from .runner import (
    InstallerError,
    Runner,
    install_cpu,
    install_gpu_managed,
)


def _root() -> Path:
    return Path.cwd().resolve()


def _paths(root: Path) -> tuple[Path, Path, Path]:
    state = root / ".museum-pipeline"
    return (
        state,
        state / "generated.env",
        state / "runtime.env",
    )


def _load(args):
    root = _root()

    deployment = load_deployment(
        args.deployment,
        root=root,
    )

    user_env = load_env(args.env)

    state, generated_path, runtime_path = _paths(root)

    secrets_env = merge_generated_secrets(
        user_env,
        generated_path,
    )

    runtime_env = build_runtime_env(
        deployment,
        secrets_env,
    )

    return (
        root,
        deployment,
        secrets_env,
        runtime_env,
        runtime_path,
    )


def install_main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="museum-pipeline install",
        description=(
            "Install the documented AI Museum Pipeline deployment."
        ),
    )
    ap.add_argument(
        "--deployment",
        default="deployment.yaml",
    )
    ap.add_argument(
        "--env",
        default=".env",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
    )
    ap.add_argument(
        "--skip-model-download",
        action="store_true",
    )

    args = ap.parse_args(argv)

    try:
        (
            root,
            deployment,
            secrets_env,
            runtime_env,
            runtime_path,
        ) = _load(args)

        write_env(
            runtime_path,
            runtime_env,
        )

        runner = Runner(
            root=root,
            dry_run=args.dry_run,
        )

        print()
        print("AI Museum Pipeline installer")
        print("=" * 72)
        print("museum profile :", deployment.museum_profile)
        print("model profile  :", deployment.model_profile)
        print("hardware       :", deployment.hardware_profile)
        print("workflow       :", deployment.workflow)
        print("GPU mode       :", deployment.gpu.mode)
        print("S3             :", deployment.features.s3)
        print("GND            :", deployment.features.gnd)
        print("dry run        :", args.dry_run)
        print("=" * 72)

        if deployment.gpu.mode == "managed":
            install_gpu_managed(
                runner,
                deployment,
                secrets_env,
                skip_model_download=args.skip_model_download,
            )

        install_cpu(
            runner,
            deployment,
            runtime_path,
            runtime_env,
        )

        if args.dry_run:
            print()
            print("INSTALL DRY-RUN: PASS")
            return 0

        checks = run_doctor(
            root,
            deployment,
            runtime_env,
        )

        if not print_doctor(checks):
            return 1

        print()
        print("INSTALLATION: READY")
        return 0

    except (
        InstallerConfigError,
        InstallerError,
        OSError,
        ValueError,
    ) as exc:
        print(f"INSTALLATION: FAIL: {exc}", file=sys.stderr)
        return 1


def doctor_main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="museum-pipeline doctor"
    )
    ap.add_argument(
        "--deployment",
        default="deployment.yaml",
    )
    ap.add_argument(
        "--env",
        default=".env",
    )
    args = ap.parse_args(argv)

    try:
        (
            root,
            deployment,
            secrets_env,
            runtime_env,
            runtime_path,
        ) = _load(args)

        write_env(
            runtime_path,
            runtime_env,
        )

        checks = run_doctor(
            root,
            deployment,
            runtime_env,
        )

        return 0 if print_doctor(checks) else 1

    except (
        InstallerConfigError,
        InstallerError,
        OSError,
        ValueError,
    ) as exc:
        print(f"DOCTOR: FAIL: {exc}", file=sys.stderr)
        return 1


def init_profile_main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="museum-pipeline init-profile"
    )
    ap.add_argument("name")
    args = ap.parse_args(argv)

    root = _root()
    source = root / "profiles/_template"
    target = root / "profiles" / args.name

    if not source.is_dir():
        print("Template profile is missing.", file=sys.stderr)
        return 1

    if target.exists():
        print(
            f"Profile already exists: {target}",
            file=sys.stderr,
        )
        return 1

    shutil.copytree(source, target)

    print(f"Created profile: {target}")
    print()
    print("Next:")
    print(f"  edit profiles/{args.name}/metadata.yaml")
    print(f"  edit profiles/{args.name}/tagging/")
    print(f"  review profiles/{args.name}/prompts/")
    print(f"  review profiles/{args.name}/authority/")
    print(
        f"  configure emotion/topics only if required"
    )

    return 0
