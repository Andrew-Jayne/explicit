#!/usr/bin/env python3
"""explicit - Enforce semantic clarity in Python code.

Targets Python 3.14 syntax and features.
"""

import sys
from pathlib import Path

from explicit.cli_args import parse_args
from explicit.constructs import Colors, StyleCheck
from explicit.file_handlers import analyze_file
from explicit.reporters import format_report, generate_statistics_report


def main() -> None:
    args = parse_args()
    if args.no_color is True or (
        args.output is not None and sys.stdout.isatty() is False
    ):
        Colors.disable()

    if args.path is None:
        sys.exit(1)

    if args.path.exists() is False:
        sys.exit(1)

    files: list[Path] = list()

    if args.path.is_file() is True:
        if (args.path.suffix == ".py") is True:
            files.append(args.path)
    elif args.path.is_dir() is True:
        for item in args.path.rglob("*.py"):
            parts: tuple[str, ...] = item.parts
            skip_dirs = {
                "__pycache__",
                ".git",
                ".venv",
                "venv",
                "env",
                "build",
                "dist",
                ".tox",
                ".pytest_cache",
            }
            should_skip: bool = False
            for part in parts:
                if (part in skip_dirs) is True:
                    should_skip = True
                    break

            if should_skip is False:
                files.append(item)

    if len(files) == 0:
        sys.exit(1)

    all_checks: list[StyleCheck] = list()
    for filepath in files:
        checks: list[StyleCheck] = analyze_file(
            filepath,
            disallow_lambda=args.disallow_lambda,
            disallow_logic_in_match=args.disallow_logic_in_match,
        )
        all_checks.extend(checks)

    if args.exclude_type is not None:
        filtered_checks: list[StyleCheck] = list()
        for check in all_checks:
            if check.check_type not in args.exclude_type:
                filtered_checks.append(check)
        all_checks = filtered_checks

    if args.stats_only is True:
        report: str = generate_statistics_report(all_checks, files)
    else:
        report = format_report(all_checks, args.format)

    if args.output is not None:
        report_no_color: str = Colors.strip_colors(report)
        args.output.write_text(report_no_color)  # pyright: ignore[reportUnusedCallResult]
    else:
        print(report)  # noqa: T201

    if len(all_checks) > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
