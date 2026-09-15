from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import os
import shlex
import shutil
import subprocess
import time
import urllib.request

from .config import (
    DeploymentConfig,
    write_env,
)


class InstallerError(RuntimeError):
    pass


@dataclass
class Runner:
    root: Path
    dry_run: bool = False
    verbose: bool = True

    def _display(self, cmd: Iterable[str]) -> None:
        if self.verbose:
            print("+", shlex.join([str(x) for x in cmd]))

    def run(
        self,
        cmd: list[str],
        *,
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
        input_text: str | None = None,
        capture: bool = False,
    ) -> subprocess.CompletedProcess:
        self._display(cmd)

        if self.dry_run:
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout="" if capture else None,
                stderr="" if capture else None,
            )

        merged = os.environ.copy()
        if env:
            merged.update(env)

        return subprocess.run(
            cmd,
            cwd=str(cwd or self.root),
            env=merged,
            input=input_text,
            text=True,
            check=True,
            capture_output=capture,
        )

    def require_commands(self, commands: list[str]) -> None:
        missing = [x for x in commands if shutil.which(x) is None]
        if missing:
            raise InstallerError(
                "Missing required command(s): " + ", ".join(missing)
            )

    def ssh_target(self, deployment: DeploymentConfig) -> str:
        return (
            f"{deployment.gpu.ssh_user}@{deployment.gpu.host}"
        )

    def _ssh_host_key_options(self) -> list[str]:
        """SSH host-key verification options, configurable via environment.

        Default is StrictHostKeyChecking=accept-new (trust-on-first-use):
        convenient, but accepts whatever host key is presented on the first
        connection to a given host (first-connect MITM window).

        For a hardened deployment, pre-pin the GPU host's key and set:

            SSH_STRICT_HOST_KEY_CHECKING=yes
            SSH_KNOWN_HOSTS_FILE=/path/to/pinned-known-hosts

        See docs/INSTALLER.md for how to generate the pinned known_hosts
        file out-of-band (e.g. via a verified console/IPMI fingerprint).
        """
        mode = os.environ.get("SSH_STRICT_HOST_KEY_CHECKING", "accept-new")
        options = ["-o", f"StrictHostKeyChecking={mode}"]
        known_hosts = os.environ.get("SSH_KNOWN_HOSTS_FILE")
        if known_hosts:
            # Passed as a literal argv element to ssh (no shell involved
            # here), so no shlex quoting -- that would add literal quote
            # characters into the filename ssh looks for.
            options += ["-o", f"UserKnownHostsFile={known_hosts}"]
        return options

    def ssh(
        self,
        deployment: DeploymentConfig,
        script: str,
    ) -> None:
        self.run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                *self._ssh_host_key_options(),
                self.ssh_target(deployment),
                "bash",
                "-s",
            ],
            input_text=script,
        )

    def scp(
        self,
        deployment: DeploymentConfig,
        source: Path,
        destination: str,
    ) -> None:
        self.run(
            [
                "scp",
                "-o",
                "BatchMode=yes",
                *self._ssh_host_key_options(),
                str(source),
                f"{self.ssh_target(deployment)}:{destination}",
            ]
        )


def cpu_compose_base(
    root: Path,
    runtime_env: Path,
) -> list[str]:
    return [
        "docker",
        "compose",
        "--env-file",
        str(runtime_env),
        "-f",
        str(root / "infra/cpu/compose.yml"),
    ]


def install_gpu_managed(
    runner: Runner,
    deployment: DeploymentConfig,
    secrets_env: dict[str, str],
    *,
    skip_model_download: bool = False,
) -> None:
    gpu = deployment.gpu
    root = runner.root

    runner.require_commands(["ssh", "scp"])

    print()
    print("GPU preflight")

    runner.ssh(
        deployment,
        """
set -u
command -v git
command -v python3
command -v docker
docker compose version
nvidia-smi
docker info >/dev/null
""",
    )

    gpu_env = {
        "GPU_COMPOSE_PROJECT": "museum-pipeline-gpu",
        "GPU_DOMAIN": gpu.domain,
        "ALLOWED_REMOTE_IP": _discover_public_ip(),
        "GPU_CONFIG_DIR": gpu.config_dir,
        "MODELS_DIR": gpu.models_dir,
        "LITELLM_MASTER_KEY": secrets_env["LITELLM_MASTER_KEY"],
        "LLAMA_SWAP_API_KEY": secrets_env["LLAMA_SWAP_API_KEY"],
    }

    ref_env = (
        root
        / gpu.deployment_path
        / ".env.example"
    )

    if ref_env.is_file():
        from .config import load_env

        reference_values = load_env(ref_env)
        for key in (
            "LLAMA_SWAP_IMAGE",
            "LITELLM_IMAGE",
            "CADDY_IMAGE",
        ):
            if reference_values.get(key):
                gpu_env[key] = reference_values[key]

    local_gpu_env = (
        root
        / ".museum-pipeline"
        / "gpu-runtime.env"
    )
    write_env(local_gpu_env, gpu_env)

    repo_url = shlex.quote(deployment.repository.url)
    repo_ref = shlex.quote(deployment.repository.ref)
    install_path = shlex.quote(gpu.install_path)
    config_dir = shlex.quote(gpu.config_dir)
    models_dir = shlex.quote(gpu.models_dir)
    deployment_path = shlex.quote(gpu.deployment_path)

    bootstrap = f"""
set -u

REPO={install_path}
REF={repo_ref}
CONFIG_DIR={config_dir}
MODELS_DIR={models_dir}
DEPLOYMENT={deployment_path}

if [ ! -d "$REPO/.git" ]; then
    git clone {repo_url} "$REPO"
fi

git -C "$REPO" fetch origin
git -C "$REPO" checkout "$REF"
git -C "$REPO" pull --ff-only origin "$REF"

mkdir -p "$CONFIG_DIR"
mkdir -p "$MODELS_DIR"

cp "$REPO/$DEPLOYMENT/llama-swap.yaml" \
   "$CONFIG_DIR/llama-swap.yaml"

cp "$REPO/$DEPLOYMENT/litellm.yaml" \
   "$CONFIG_DIR/litellm.yaml"
"""

    runner.ssh(deployment, bootstrap)

    # Below, use the already shlex.quote()d local variables (install_path,
    # config_dir, models_dir, deployment_path) rather than the raw gpu.*
    # attributes -- these strings are embedded into remote bash scripts and
    # a maliciously crafted deployment.yaml must not be able to break out
    # of the intended shell context.
    runner.scp(
        deployment,
        local_gpu_env,
        f"{gpu.config_dir}/runtime.env",
    )

    runner.ssh(
        deployment,
        f"chmod 600 {config_dir}/runtime.env",
    )

    if not skip_model_download:
        download_script = f"""
set -u
python3 {install_path}/{deployment_path}/download-models.py \
  --models-dir {models_dir}
"""
        runner.ssh(deployment, download_script)

    compose_script = f"""
set -u

cd {install_path}

docker compose \
  --env-file {config_dir}/runtime.env \
  -f infra/gpu/generic/compose.yml \
  config >/dev/null

docker compose \
  --env-file {config_dir}/runtime.env \
  -f infra/gpu/generic/compose.yml \
  up -d
"""

    runner.ssh(deployment, compose_script)

    if not runner.dry_run:
        _wait_https(
            f"https://{gpu.domain}/v1/models",
            token=secrets_env["LITELLM_MASTER_KEY"],
            attempts=60,
        )


def _discover_public_ip() -> str:
    override = os.environ.get("INSTALLER_ALLOWED_REMOTE_IP", "").strip()
    if override:
        return override

    try:
        with urllib.request.urlopen(
            "https://api.ipify.org",
            timeout=10,
        ) as response:
            value = response.read().decode("utf-8").strip()
            if value:
                return value
    except Exception as exc:
        raise InstallerError(
            "Could not determine CPU public IP. "
            "Set INSTALLER_ALLOWED_REMOTE_IP."
        ) from exc

    raise InstallerError(
        "Could not determine CPU public IP. "
        "Set INSTALLER_ALLOWED_REMOTE_IP."
    )


def _wait_https(
    url: str,
    *,
    token: str,
    attempts: int,
) -> None:
    last: Exception | None = None

    for _ in range(attempts):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )
            with urllib.request.urlopen(
                request,
                timeout=10,
            ) as response:
                if response.status == 200:
                    return
        except Exception as exc:
            last = exc

        time.sleep(5)

    raise InstallerError(
        f"GPU endpoint did not become ready: {url}: {last}"
    )


def install_cpu(
    runner: Runner,
    deployment: DeploymentConfig,
    runtime_env: Path,
    process_env: dict[str, str],
) -> None:
    root = runner.root

    runner.require_commands(
        [
            "docker",
            "curl",
        ]
    )

    runner.run(["docker", "compose", "version"])

    base = cpu_compose_base(root, runtime_env)

    cmd = list(base)

    if deployment.features.s3:
        cmd += ["--profile", "s3"]

    if deployment.features.gnd:
        cmd += ["--profile", "gnd"]

    cmd += ["up", "-d", "--build", "postgres", "embeddings"]

    if deployment.features.s3:
        cmd.append("presign")

    if deployment.features.gnd:
        cmd.append("gnd_opensearch")

    runner.run(cmd)

    if runner.dry_run:
        return

    _wait_postgres(
        runner,
        base,
        process_env,
    )
    _wait_http("http://127.0.0.1:8081/health")

    if deployment.features.s3:
        _wait_http("http://127.0.0.1:8082/health")

    if deployment.features.gnd:
        _wait_http("http://127.0.0.1:9200/_cluster/health")

    _apply_sql(
        runner,
        base,
        root / "database/core.sql",
    )

    if deployment.workflow in {"core-emotion", "full"}:
        _apply_sql(
            runner,
            base,
            root / "database/modules/emotion.sql",
        )

    if deployment.workflow in {"core-topics", "full"}:
        _apply_sql(
            runner,
            base,
            root / "database/modules/topics.sql",
        )

    _apply_profile_sql(
        runner,
        deployment,
        base,
    )

    if deployment.features.gnd:
        _install_gnd(runner, process_env)

    runner.run(
        [
            str(root / ".venv/bin/museum-pipeline"),
            "validate-config",
        ],
        env=process_env,
    )


def _wait_postgres(
    runner: Runner,
    base: list[str],
    process_env: dict[str, str],
) -> None:
    user = process_env.get("PG_USER", "museum")
    database = process_env.get("PG_DB", "museum")

    for _ in range(60):
        result = subprocess.run(
            base
            + [
                "exec",
                "-T",
                "postgres",
                "pg_isready",
                "-U",
                user,
                "-d",
                database,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if result.returncode == 0:
            return

        time.sleep(2)

    raise InstallerError("PostgreSQL did not become ready")


def _wait_http(url: str) -> None:
    last: Exception | None = None

    for _ in range(60):
        try:
            with urllib.request.urlopen(
                url,
                timeout=10,
            ) as response:
                if 200 <= response.status < 300:
                    return
        except Exception as exc:
            last = exc
        time.sleep(2)

    raise InstallerError(f"Service not ready: {url}: {last}")


def _apply_sql(
    runner: Runner,
    base: list[str],
    sql_path: Path,
) -> None:
    if not sql_path.is_file():
        raise InstallerError(f"SQL file missing: {sql_path}")

    sql = sql_path.read_text(encoding="utf-8")

    runner.run(
        base
        + [
            "exec",
            "-T",
            "postgres",
            "sh",
            "-c",
            'psql -v ON_ERROR_STOP=1 '
            '-U "$POSTGRES_USER" '
            '-d "$POSTGRES_DB"',
        ],
        input_text=sql,
    )


def _apply_profile_sql(
    runner: Runner,
    deployment: DeploymentConfig,
    base: list[str],
) -> None:
    profile_root = (
        runner.root
        / "profiles"
        / deployment.museum_profile
    )

    manifest = profile_root / "install.yaml"

    if not manifest.is_file():
        return

    import yaml

    data = yaml.safe_load(
        manifest.read_text(encoding="utf-8")
    ) or {}

    paths = data.get("database_sql") or []

    if not isinstance(paths, list):
        raise InstallerError(
            f"{manifest}: database_sql must be a list"
        )

    for rel in paths:
        candidate = (profile_root / str(rel)).resolve()

        if profile_root.resolve() not in candidate.parents:
            raise InstallerError(
                f"Profile SQL escapes profile directory: {rel}"
            )

        _apply_sql(runner, base, candidate)


def _install_gnd(
    runner: Runner,
    process_env: dict[str, str],
) -> None:
    root = runner.root
    target = (
        root
        / "data/gnd/authorities-gnd-sachbegriff_lds.jsonld.gz"
    )
    target.parent.mkdir(parents=True, exist_ok=True)

    runner.run(
        [
            "curl",
            "-fL",
            "--retry",
            "5",
            "-o",
            str(target),
            "https://data.dnb.de/opendata/"
            "authorities-gnd-sachbegriff_lds.jsonld.gz",
        ]
    )

    env = dict(process_env)
    env["GND_INPUT_FILE"] = str(target)

    runner.run(
        [
            str(root / ".venv/bin/python"),
            str(root / "tools/import_gnd_subjects.py"),
        ],
        env=env,
    )
