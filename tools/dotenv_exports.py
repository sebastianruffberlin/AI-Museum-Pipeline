#!/usr/bin/env python3
"""
Convert a simple dotenv file to safely quoted POSIX-shell export statements.

Usage:

    eval "$(.venv/bin/python tools/dotenv_exports.py .env)"

The dotenv file is parsed as DATA. It is never sourced or executed.

Supported:
- blank lines
- comments beginning with #
- KEY=value
- optional matching single/double quotes around the whole value
- whitespace and shell metacharacters inside values

Intentionally unsupported:
- shell command substitution
- variable expansion
- shell functions
- arbitrary shell syntax

This keeps one .env usable for Docker Compose and for manual host-side CLI
commands without treating secrets or configuration values as shell code.
"""

from __future__ import annotations

import re
import shlex
import sys
from pathlib import Path


KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def parse_env(path: Path) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    seen: set[str] = set()

    for lineno, raw in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw.rstrip("\r")

        if not line.strip():
            continue

        if line.lstrip().startswith("#"):
            continue

        if "=" not in line:
            raise ValueError(
                f"{path}:{lineno}: expected KEY=value"
            )

        key, value = line.split("=", 1)
        key = key.strip()

        if not KEY_RE.fullmatch(key):
            raise ValueError(
                f"{path}:{lineno}: invalid environment key {key!r}"
            )

        if key in seen:
            raise ValueError(
                f"{path}:{lineno}: duplicate environment key {key!r}"
            )

        # Keep whitespace inside the value; remove only surrounding
        # formatting whitespace.
        value = value.strip()

        # Matching quotes are dotenv syntax here, not shell syntax.
        # They are removed as data and never evaluated.
        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        values.append((key, value))
        seen.add(key)

    return values


def main() -> int:
    if len(sys.argv) != 2:
        print(
            "usage: dotenv_exports.py PATH_TO_ENV",
            file=sys.stderr,
        )
        return 2

    path = Path(sys.argv[1])

    if not path.is_file():
        print(
            f"dotenv file not found: {path}",
            file=sys.stderr,
        )
        return 2

    try:
        values = parse_env(path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    for key, value in values:
        print(f"export {key}={shlex.quote(value)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
