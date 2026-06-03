#!/usr/bin/env python3
"""explicit - Enforce semantic clarity in Python code.

Targets Python 3.14 syntax and features.
"""

import sys
from pathlib import Path
from typing import NamedTuple

from explicit.cli_args import Args, parse_args
from explicit.config import Config, load_config
from explicit.constructs import Colors, ReportFormat, StyleCheck
from explicit.file_handlers import analyze_file
from explicit.reporters import format_report, generate_statistics_report


class Settings(NamedTuple):
    """The effective configuration after merging CLI flags over the config file."""

    no_color: bool
    stats_only: bool
    output_format: ReportFormat
    exclude_type: list[str]
    include_extra: set[str]


def _resolve_bool(cli_value: bool | None, config_value: bool | None) -> bool:
    if cli_value is not None:
        return cli_value
    if config_value is not None:
        return config_value
    return False


def _resolve_format(
    cli_value: ReportFormat | None, config_value: ReportFormat | None
) -> ReportFormat:
    if cli_value is not None:
        return cli_value
    if config_value is not None:
        return config_value
    return ReportFormat.TEXT


def _merge_list(
    cli_value: list[str] | None, config_value: list[str] | None
) -> list[str]:
    merged: list[str] = list()
    if config_value is not None:
        merged.extend(config_value)
    if cli_value is not None:
        merged.extend(cli_value)
    return merged


def _resolve_settings(args: Args, config: Config) -> Settings:
    return Settings(
        no_color=_resolve_bool(args.no_color, config.no_color),
        stats_only=_resolve_bool(args.stats_only, config.stats_only),
        output_format=_resolve_format(args.format, config.format),
        exclude_type=_merge_list(args.exclude_type, config.exclude_type),
        include_extra=set(_merge_list(args.include_extra, config.include_extra)),
    )


def main() -> None:
    args = parse_args()

    if args.path is None:
        sys.exit(1)

    if args.path.exists() is False:
        sys.exit(1)

    config = load_config(args.path, args.config)
    settings = _resolve_settings(args, config)

    if settings.no_color is True or (
        args.output is not None and sys.stdout.isatty() is False
    ):
        Colors.disable()

    files: list[Path] = list()

    if args.path.is_file() is True:
        if (args.path.suffix == ".py") is True:
            files.append(args.path)
    elif args.path.is_dir() is True:
        for item in args.path.rglob("*.py"):
            should_skip: bool = False
            for part in item.parts:
                if part in {
                    "__pycache__",
                    ".git",
                    ".venv",
                    "venv",
                    "env",
                    "build",
                    "dist",
                    ".tox",
                    ".pytest_cache",
                }:
                    should_skip = True
                    break

            if should_skip is False:
                files.append(item)

    if len(files) == 0:
        sys.exit(1)

    all_checks: list[StyleCheck] = list()
    for filepath in files:
        all_checks.extend(
            analyze_file(
                filepath,
                include_extra=settings.include_extra,
                entry_points=config.entry_points,
            )
        )

    if len(settings.exclude_type) > 0:
        filtered_checks: list[StyleCheck] = list()
        for check in all_checks:
            if check.check_type not in settings.exclude_type:
                filtered_checks.append(check)
        all_checks = filtered_checks

    if settings.stats_only is True:
        report: str = generate_statistics_report(all_checks, files)
    else:
        report = format_report(all_checks, settings.output_format)

    if args.output is not None:
        args.output.write_text(Colors.strip_colors(report))  # pyright: ignore[reportUnusedCallResult]
    else:
        print(report)  # noqa: T201

    if len(all_checks) > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
