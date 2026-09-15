from __future__ import annotations

import sys


def main() -> int:
    argv = sys.argv[1:]

    if argv:
        command = argv[0]
        rest = argv[1:]

        if command == "install":
            from museum_pipeline.installer.cli import install_main
            return install_main(rest)

        if command == "doctor":
            from museum_pipeline.installer.cli import doctor_main
            return doctor_main(rest)

        if command == "init-profile":
            from museum_pipeline.installer.cli import init_profile_main
            return init_profile_main(rest)

    # Existing CLI stays completely unchanged.
    from museum_pipeline.cli import main as original_main
    return original_main()


if __name__ == "__main__":
    raise SystemExit(main())
