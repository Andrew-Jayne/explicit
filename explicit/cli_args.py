import argparse
from pathlib import Path

from explicit.constructs import CheckType, ReportFormat


class Args(argparse.Namespace):
    """Typed namespace for parsed command-line arguments."""

    path: Path | None = None
    format: ReportFormat = ReportFormat.TEXT
    exclude_type: list[str] | None = None
    output: Path | None = None
    stats_only: bool = False
    disallow_lambda: bool = False
    disallow_logic_in_match: bool = False
    no_color: bool = False

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
        "-f",
        "--format",
        choices=list(ReportFormat),
        default=ReportFormat.TEXT,
        type=ReportFormat,
        help="Output format (default: text)",
    )

    parser.add_argument(  # pyright: ignore[reportUnusedCallResult]
        "--exclude-type",
        action="append",
        choices=list(CheckType),
        help="Exclude specific types of checks (can be used multiple times)",
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
        help="Show only statistics, not individual checks",
    )

    parser.add_argument(  # pyright: ignore[reportUnusedCallResult]
        "--disallow-lambda",
        action="store_true",
        help="Disallow ALL lambda expressions (they should be named functions)",
    )

    parser.add_argument(  # pyright: ignore[reportUnusedCallResult]
        "--disallow-logic-in-match",
        action="store_true",
        help=(
            "Disallow guards (if conditions) in match/case statements - "
            "logic should be in case body"
        ),
    )

    parser.add_argument(  # pyright: ignore[reportUnusedCallResult]
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

    return parser


def parse_args() -> Args:
    parser = build_parser()
    return parser.parse_args(namespace=Args())
