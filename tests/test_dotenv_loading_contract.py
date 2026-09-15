from __future__ import annotations

import runpy
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "tools" / "dotenv_exports.py"


def test_dotenv_exports_preserves_values_with_spaces(tmp_path):
    envfile = tmp_path / ".env"

    envfile.write_text(
        "\n".join(
            [
                "LCPP_AUTH=Bearer example-token",
                "OPENSEARCH_JAVA_OPTS=-Xms2g -Xmx2g",
                "PLAIN=value",
                "",
            ]
        ),
        encoding="utf-8",
    )

    command = (
        f'eval "$({sys.executable} {HELPER} {envfile})"; '
        f'{sys.executable} -c '
        '"import os; '
        "assert os.environ['LCPP_AUTH'] == 'Bearer example-token'; "
        "assert os.environ['OPENSEARCH_JAVA_OPTS'] == '-Xms2g -Xmx2g'; "
        "assert os.environ['PLAIN'] == 'value'\""
    )

    result = subprocess.run(
        ["bash", "-c", command],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stderr


def test_dotenv_exports_does_not_execute_shell_syntax(tmp_path):
    envfile = tmp_path / ".env"

    envfile.write_text(
        "VALUE=$(printf SHOULD_NOT_EXECUTE)\n",
        encoding="utf-8",
    )

    command = (
        f'eval "$({sys.executable} {HELPER} {envfile})"; '
        'test "$VALUE" = \'$(printf SHOULD_NOT_EXECUTE)\''
    )

    result = subprocess.run(
        ["bash", "-c", command],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stderr


def test_markdown_code_blocks_do_not_source_dotenv():
    violations = []

    for path in ROOT.rglob("*.md"):
        if ".git" in path.parts:
            continue

        in_fence = False

        for lineno, raw in enumerate(
            path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            stripped = raw.strip()

            if stripped.startswith("```"):
                in_fence = not in_fence
                continue

            if not in_fence:
                continue

            if stripped in {
                "source .env",
                "source ./.env",
                ". .env",
                ". ./.env",
            }:
                violations.append(
                    f"{path.relative_to(ROOT)}:{lineno}:{stripped}"
                )

    assert not violations, "\n".join(violations)


def test_reference_env_documents_full_authorization_header():
    namespace = runpy.run_path(str(HELPER))

    values = dict(
        namespace["parse_env"](ROOT / ".env.example")
    )

    assert values["LCPP_AUTH"] == "Bearer CHANGE_ME"
    assert values["OPENSEARCH_JAVA_OPTS"] == "-Xms2g -Xmx2g"

def test_cpu_manual_documents_safe_dotenv_loader():
    text = (
        ROOT / "infra" / "cpu" / "INSTALL.md"
    ).read_text(encoding="utf-8")

    assert "tools/dotenv_exports.py .env" in text
