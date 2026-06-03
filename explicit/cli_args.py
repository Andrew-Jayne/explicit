import argparse
from importlib.metadata import version
from pathlib import Path

from explicit.constructs import EXTRA_CHECKS, CheckType, ReportFormat


class Args(argparse.Namespace):
    """Typed namespace for parsed command-line arguments.

    Flag-backed fields default to None ("not specified") so a pyproject
    [tool.explicit] table can supply a value when the flag is absent. Resolution
    happens in main.py, where the CLI always wins over the config file.
    """

    path: Path | None = None
    config: Path | None = None
    format: ReportFormat | None = None
    exclude_type: list[str] | None = None
    include_extra: list[str] | None = None
    output: Path | None = None
    stats_only: bool | None = None
    no_color: bool | None = None

    def __init__(self) -> None:
        argparse.Namespace.__init__(self)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Enforce semantic clarity in Python code",
        epilog="Examples:\n"
        + "  %(prog)s myfile.py\n"
        + "  %(prog)s /path/to/project\n"
        + "  %(prog)s . --format json\n"
        + "  %(prog)s src/ --exclude-type ternary",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("path", type=Path, help="Python file or directory to analyze")  # pyright: ignore[reportUnusedCallResult]

    parser.add_argument(  # pyright: ignore[reportUnusedCallResult]
        "--version",
        action="version",
        version=f"%(prog)s {version('explicit')}",
    )

    parser.add_argument(  # pyright: ignore[reportUnusedCallResult]
        "--config",
        type=Path,
        help="Path to a pyproject.toml to read [tool.explicit] from "
        "(default: discovered by walking up from the analyzed path)",
    )

    parser.add_argument(  # pyright: ignore[reportUnusedCallResult]
        "-f",
        "--format",
        choices=list(ReportFormat),
        default=None,
        type=ReportFormat,
        help="Output format (default: text)",
    )

    parser.add_argument(  # pyright: ignore[reportUnusedCallResult]
        "--exclude-type",
        action="append",
        choices=list(CheckType),
        help="Turn a check off entirely (can be used multiple times)",
    )

    parser.add_argument(  # pyright: ignore[reportUnusedCallResult]
        "--include-extra",
        action="append",
        choices=sorted(EXTRA_CHECKS),
        help="Opt into a stricter check that flags every occurrence, not just "
        "ambiguous ones: 'lambda' bans all lambdas, 'match_guard' bans all "
        "match/case guards (can be used multiple times)",
    )

    parser.add_argument(  # pyright: ignore[reportUnusedCallResult]
        "-o",
        "--output",
        type=Path,
        help="Output file (default: stdout)",
    )

    parser.add_argument(  # pyright: ignore[reportUnusedCallResult]
        "--stats-only",
        action="store_true",
        default=None,
        help="Show only statistics, not individual checks",
    )

    parser.add_argument(  # pyright: ignore[reportUnusedCallResult]
        "--no-color",
        action="store_true",
        default=None,
        help="Disable colored output",
    )

    return parser


def parse_args() -> Args:
    return build_parser().parse_args(namespace=Args())
