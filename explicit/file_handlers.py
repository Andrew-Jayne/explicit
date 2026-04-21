from ast import parse
from pathlib import Path

from explicit.code_visitor import NodeVisitor
from explicit.constructs import StyleCheck
from explicit.single_use import find_single_use


def analyze_file(
    filepath: Path,
    *,
    disallow_lambda: bool = False,
    disallow_logic_in_match: bool = False,
) -> list[StyleCheck]:
    source = filepath.read_text(encoding="utf-8")
    tree = parse(source, filename=str(filepath))
    finder = NodeVisitor(
        filename=str(filepath),
        disallow_lambda=disallow_lambda,
        disallow_logic_in_match=disallow_logic_in_match,
    )
    checks = list(finder.visit(tree))
    checks.extend(find_single_use(tree, str(filepath)))
    return checks
