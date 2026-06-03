import csv
import io
import json
from itertools import groupby
from pathlib import Path

from explicit.constructs import Colors, ReportFormat, StyleCheck


# Color mapping for check types
TYPE_COLORS: dict[str, str] = {
    "if": Colors.YELLOW,
    "while": Colors.YELLOW,
    "assert": Colors.RED,
    "ternary": Colors.CYAN,
    "bool_op": Colors.BLUE,
    "list_comp": Colors.MAGENTA,
    "dict_comp": Colors.MAGENTA,
    "set_comp": Colors.MAGENTA,
    "generator": Colors.MAGENTA,
    "lambda": Colors.CYAN,
    "filter": Colors.BLUE,
    "match_guard": Colors.YELLOW,
    "dict_get": Colors.BLUE,
    "single_letter_var": Colors.RED,
    "single_use_var": Colors.GREEN,
    "single_use_func": Colors.GREEN,
}


def _sort_by_file_line(check: StyleCheck) -> tuple[str, int]:
    return (check.file, check.line)


def _group_by_file(check: StyleCheck) -> str:
    return check.file


def _sort_by_count_desc(item: tuple[str, int]) -> int:
    return -item[1]


def format_report(
    checks: list[StyleCheck],
    format_type: ReportFormat = ReportFormat.TEXT,
) -> str:
    """Format the report of style checks."""

    match format_type:
        case ReportFormat.JSON:
            check_list: list[dict[str, str]] = list()
            for check in checks:
                check_list.append(check._asdict())
            return json.dumps(check_list, indent=2)

        case ReportFormat.CSV:
            csv_output = io.StringIO()
            writer = csv.writer(csv_output)
            writer.writerow(["File", "Line", "Column", "Type", "Code", "Context"])
            for check in checks:
                writer.writerow(
                    [
                        check.file,
                        check.line,
                        check.column,
                        check.check_type,
                        check.code,
                        check.context,
                    ]
                )
            return csv_output.getvalue()
        case ReportFormat.TEXT:
            # text format
            if len(checks) == 0:
                return f"{Colors.GREEN}✓ No style violatons found.{Colors.RESET}"

            output: list[str] = list()

            output.append(
                f"\n{Colors.BOLD}{Colors.RED}Found {len(checks)} "
                f"style violaton(s):{Colors.RESET}\n"
            )
            output.append(f"{Colors.GRAY}{'─' * 80}{Colors.RESET}")

            for file, file_checks in groupby(
                sorted(checks, key=_sort_by_file_line), key=_group_by_file
            ):
                output.append(f"\n{Colors.BOLD}{Colors.BLUE}📄 {file}{Colors.RESET}")
                for check in file_checks:
                    output.append(
                        f"  {Colors.GRAY}Line {Colors.RESET}"
                        f"{Colors.BOLD}{check.line}{Colors.RESET}"
                        f"{Colors.GRAY}:{Colors.RESET}{check.column} "
                        f"{TYPE_COLORS.get(check.check_type, Colors.WHITE)}[{check.check_type}]{Colors.RESET}"
                    )
                    output.append(
                        f"    {Colors.DIM}Code:{Colors.RESET} "
                        f"{Colors.WHITE}{check.code}{Colors.RESET}"
                    )
                    output.append(
                        f"    {Colors.DIM}Context:{Colors.RESET} {check.context}"
                    )
                    output.append("")

            # Statistics
            output.append(f"{Colors.GRAY}{'─' * 80}{Colors.RESET}")
            output.append(f"\n{Colors.BOLD}{Colors.CYAN}📊 Statistics:{Colors.RESET}")
            type_counts: dict[str, int] = dict()
            for check in checks:
                type_counts[check.check_type] = type_counts.get(check.check_type, 0) + 1

            for check_type, count in sorted(type_counts.items()):
                output.append(
                    f"  {TYPE_COLORS.get(check_type, Colors.WHITE)}{check_type:20}{Colors.RESET} "
                    f"{Colors.BOLD}{count}{Colors.RESET}"
                )

            return "\n".join(output)
        case _:
            raise ValueError


def generate_statistics_report(all_checks: list[StyleCheck], files: list[Path]) -> str:
    """Generate statistics-only report.

    Args:
        all_checks: All checks found
        files: Files analyzed

    Returns:
        Statistics report string

    """
    output: list[str] = list()
    output.append(f"\n{Colors.BOLD}{Colors.CYAN}📊 Check Statistics{Colors.RESET}")
    output.append(f"{Colors.GRAY}{'═' * 50}{Colors.RESET}")
    output.append(
        f"{Colors.BOLD}Total files analyzed:{Colors.RESET} "
        f"{Colors.BLUE}{len(files)}{Colors.RESET}"
    )

    if len(all_checks) == 0:
        checks_line: str = (
            f"{Colors.BOLD}Total checks found:{Colors.RESET} "
            f"{Colors.GREEN}0{Colors.RESET} {Colors.GREEN}✓{Colors.RESET}"
        )
        output.append(checks_line)
    else:
        checks_line = (
            f"{Colors.BOLD}Total checks found:{Colors.RESET} "
            f"{Colors.RED}{len(all_checks)}{Colors.RESET}"
        )
        output.append(checks_line)
    output.append("")

    type_counts: dict[str, int] = dict()
    # this is a very awkward way of incrementing a value and is rather opaue in its intent
    for check in all_checks:
        type_counts[check.check_type] = type_counts.get(check.check_type, 0) + 1

    if len(all_checks) > 0:
        output.append(f"{Colors.BOLD}By type:{Colors.RESET}")
        for check_type, count in sorted(type_counts.items(), key=_sort_by_count_desc):
            percentage = count / len(all_checks) * 100
            output.append(
                f"  {TYPE_COLORS.get(check_type, Colors.WHITE)}{check_type:20}{Colors.RESET} "
                + f"{Colors.BOLD}{count:5}{Colors.RESET} "
                + f"{Colors.GRAY}({percentage:5.1f}%){Colors.RESET} "
                + f"{TYPE_COLORS.get(check_type, Colors.WHITE)}{'█' * int(percentage / 2)}{Colors.RESET}"
            )

    return "\n".join(output)
