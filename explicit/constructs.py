import re
from enum import StrEnum
from typing import NamedTuple


class ReportFormat(StrEnum):
    TEXT = "text"
    JSON = "json"
    CSV = "csv"


class CheckType(StrEnum):
    IF = "if"
    WHILE = "while"
    ASSERT = "assert"
    TERNARY = "ternary"
    BOOL_OP = "bool_op"
    COMPREHENSION = "comprehension"
    LIST_COMP = "list_comp"
    SET_COMP = "set_comp"
    DICT_COMP = "dict_comp"
    GENERATOR = "generator"
    LAMBDA = "lambda"
    FILTER = "filter"
    MATCH_GUARD = "match_guard"
    SINGLE_LETTER_VAR = "single_letter_var"
    SINGLE_USE_VAR = "single_use_var"
    SINGLE_USE_FUNC = "single_use_func"


# ANSI color codes for terminal output
## this should be an enum with a .value access shortcut
class Colors:
    """ANSI escape codes for terminal colors."""

    RESET: str = "\033[0m"
    BOLD: str = "\033[1m"
    DIM: str = "\033[2m"

    # Foreground colors
    RED: str = "\033[91m"
    GREEN: str = "\033[92m"
    YELLOW: str = "\033[93m"
    BLUE: str = "\033[94m"
    MAGENTA: str = "\033[95m"
    CYAN: str = "\033[96m"
    WHITE: str = "\033[97m"
    GRAY: str = "\033[90m"

    # Background colors
    BG_RED: str = "\033[101m"
    BG_GREEN: str = "\033[102m"
    BG_YELLOW: str = "\033[103m"
    BG_BLUE: str = "\033[104m"
    _colors_enabled: bool = True

    @staticmethod
    def strip_colors(text: str) -> str:
        """Remove ANSI color codes from text."""
        ansi_escape = re.compile(r"\033\[[0-9;]+m")
        return ansi_escape.sub("", text)

    @classmethod
    def disable(cls) -> None:
        cls._colors_enabled = False


class StyleCheck(NamedTuple):
    """Represents a style check found in the code."""

    file: str
    line: int
    column: int
    code: str
    context: str
    check_type: CheckType
