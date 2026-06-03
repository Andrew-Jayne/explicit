from ast import parse
from pathlib import Path

from explicit.code_visitor import NodeVisitor
from explicit.constructs import StyleCheck
from explicit.single_use import find_single_use


def analyze_file(
    filepath: Path,
    *,
    include_extra: set[str] | None = None,
    entry_points: set[str] | None = None,
) -> list[StyleCheck]:
    tree = parse(filepath.read_text(encoding="utf-8"), filename=str(filepath))
    checks = list(
        NodeVisitor(
            filename=str(filepath),
            include_extra=include_extra,
        ).visit(tree)
    )
    checks.extend(find_single_use(tree, str(filepath), entry_points))
    return checks
