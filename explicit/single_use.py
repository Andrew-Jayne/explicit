import ast
from typing import cast

from explicit.constructs import CheckType, StyleCheck


MAX_CODE_LENGTH = 100
EXCLUDED_NAMES = {"_"}


def find_single_use(
    tree: ast.Module,
    filename: str,
    entry_points: set[str] | None = None,
) -> list[StyleCheck]:
    if entry_points is None:
        entry_points = set()
    results: list[StyleCheck] = list()
    _analyze_scope(tree.body, filename, results, entry_points=entry_points)
    return results


def _is_dunder(name: str) -> bool:
    return (
        len(name) > 4 and name.startswith("__") is True and name.endswith("__") is True
    )


def _has_letter(name: str) -> bool:
    for char in name:
        if char.isalpha() is True:
            return True
    return False


def _is_constant(name: str) -> bool:
    if name.isupper() is False:
        return False
    return _has_letter(name)


def _is_main_guard(stmt: ast.stmt) -> bool:
    if isinstance(stmt, ast.If) is False:
        return False
    test = cast(ast.If, stmt).test
    if isinstance(test, ast.Compare) is False:
        return False
    compare = cast(ast.Compare, test)
    operands: list[ast.expr] = [compare.left]
    operands.extend(compare.comparators)
    has_name = False
    has_main = False
    for operand in operands:
        if isinstance(operand, ast.Name) is True:
            if cast(ast.Name, operand).id == "__name__":
                has_name = True
        if isinstance(operand, ast.Constant) is True:
            if cast(ast.Constant, operand).value == "__main__":
                has_main = True
    return has_name is True and has_main is True


def _collect_loaded_names(node: ast.AST, names: set[str]) -> None:
    if isinstance(node, ast.Name) is True:
        if isinstance(cast(ast.Name, node).ctx, ast.Load) is True:
            names.add(cast(ast.Name, node).id)
    for child in ast.iter_child_nodes(node):
        _collect_loaded_names(child, names)


def _collect_main_guard_names(body: list[ast.stmt]) -> set[str]:
    names: set[str] = set()
    for stmt in body:
        if _is_main_guard(stmt) is True:
            for inner in cast(ast.If, stmt).body:
                _collect_loaded_names(inner, names)
    return names


def _analyze_scope(
    body: list[ast.stmt],
    filename: str,
    results: list[StyleCheck],
    *,
    entry_points: set[str],
    is_class: bool = False,
) -> None:
    _recurse_into_nested_scopes(body, filename, results, entry_points)

    if is_class is True:
        return

    var_defs: dict[str, list[tuple[int, int]]] = dict()
    func_defs: dict[str, list[tuple[int, int, bool]]] = dict()
    excluded: set[str] = set()
    refs: dict[str, int] = dict()

    for stmt in body:
        _walk_for_var_defs(stmt, var_defs)
        _walk_for_func_defs(stmt, func_defs)
        _walk_for_excluded(stmt, excluded)
        _walk_for_refs(stmt, refs)

    # A function invoked only from this scope's `if __name__ == "__main__":`
    # guard is an entry point too, so fold those names into the exemption set.
    entry_points = entry_points | _collect_main_guard_names(body)

    for name, positions in var_defs.items():
        if name in EXCLUDED_NAMES or name in excluded or _is_dunder(name) is True:
            continue
        if _is_constant(name) is True:
            continue
        if len(positions) == 1 and refs.get(name, 0) == 1:
            line, col = positions[0]
            results.append(
                StyleCheck(
                    file=filename,
                    line=line,
                    column=col,
                    code=name,
                    context=f"Variable '{name}' is only used once - consider inlining the expression",
                    check_type=CheckType.SINGLE_USE_VAR,
                )
            )

    for name, positions in func_defs.items():
        if name in excluded or _is_dunder(name) is True:
            continue
        if name in entry_points:
            continue
        if len(positions) == 1:
            line, col, has_decorator = positions[0]
            if has_decorator is True:
                continue
            if refs.get(name, 0) == 1:
                results.append(
                    StyleCheck(
                        file=filename,
                        line=line,
                        column=col,
                        code=f"def {name}(...)",
                        context=f"Function '{name}' is only used once - consider inlining at the call site",
                        check_type=CheckType.SINGLE_USE_FUNC,
                    )
                )


def _recurse_into_nested_scopes(
    body: list[ast.stmt],
    filename: str,
    results: list[StyleCheck],
    entry_points: set[str],
) -> None:
    for stmt in body:
        _find_nested_scopes(stmt, filename, results, entry_points)


def _find_nested_scopes(
    node: ast.AST,
    filename: str,
    results: list[StyleCheck],
    entry_points: set[str],
) -> None:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) is True:
        _analyze_scope(
            cast(ast.FunctionDef, node).body,
            filename,
            results,
            entry_points=entry_points,
        )
        return
    if isinstance(node, ast.ClassDef) is True:
        _analyze_scope(
            cast(ast.ClassDef, node).body,
            filename,
            results,
            entry_points=entry_points,
            is_class=True,
        )
        return
    for child in ast.iter_child_nodes(node):
        _find_nested_scopes(child, filename, results, entry_points)


def _walk_for_var_defs(
    node: ast.AST,
    var_defs: dict[str, list[tuple[int, int]]],
) -> None:
    if isinstance(node, ast.Assign) is True:
        for target in cast(ast.Assign, node).targets:
            if isinstance(target, ast.Name) is True:
                name_target = cast(ast.Name, target)
                var_defs.setdefault(name_target.id, list()).append(
                    (name_target.lineno, name_target.col_offset)
                )
    elif isinstance(node, ast.AnnAssign) is True:
        ann = cast(ast.AnnAssign, node)
        if isinstance(ann.target, ast.Name) is True and ann.value is not None:
            ann_target = cast(ast.Name, ann.target)
            var_defs.setdefault(ann_target.id, list()).append(
                (ann_target.lineno, ann_target.col_offset)
            )

    if (
        isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        )
        is True
    ):
        return

    for child in ast.iter_child_nodes(node):
        _walk_for_var_defs(child, var_defs)


def _walk_for_func_defs(
    node: ast.AST,
    func_defs: dict[str, list[tuple[int, int, bool]]],
) -> None:
    if isinstance(node, ast.AsyncFunctionDef) is True:
        return
    if isinstance(node, ast.FunctionDef) is True:
        func = cast(ast.FunctionDef, node)
        if func.name == "main":
            return
        func_defs.setdefault(func.name, list()).append(
            (func.lineno, func.col_offset, len(func.decorator_list) > 0)
        )
        return

    if isinstance(node, (ast.ClassDef, ast.Lambda)) is True:
        return

    for child in ast.iter_child_nodes(node):
        _walk_for_func_defs(child, func_defs)


def _walk_for_excluded(node: ast.AST, excluded: set[str]) -> None:
    if isinstance(node, ast.Global) is True:
        excluded.update(cast(ast.Global, node).names)
    elif isinstance(node, ast.Nonlocal) is True:
        excluded.update(cast(ast.Nonlocal, node).names)

    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) is True:
        _collect_nonlocals_from_nested(node, excluded)
        return

    if isinstance(node, (ast.ClassDef, ast.Lambda)) is True:
        return

    for child in ast.iter_child_nodes(node):
        _walk_for_excluded(child, excluded)


def _collect_nonlocals_from_nested(node: ast.AST, excluded: set[str]) -> None:
    for child in ast.iter_child_nodes(node):
        if (
            isinstance(
                child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
            )
            is True
        ):
            continue
        if isinstance(child, ast.Nonlocal) is True:
            excluded.update(cast(ast.Nonlocal, child).names)
        _collect_nonlocals_from_nested(child, excluded)


def _walk_for_refs(node: ast.AST, refs: dict[str, int]) -> None:
    if isinstance(node, ast.Name) is True:
        if isinstance(cast(ast.Name, node).ctx, ast.Load) is True:
            name = cast(ast.Name, node).id
            refs[name] = refs.get(name, 0) + 1

    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) is True:
        func = cast(ast.FunctionDef, node)
        for decorator in func.decorator_list:
            _walk_for_refs(decorator, refs)
        for default in func.args.defaults:
            _walk_for_refs(default, refs)
        for kw_default in func.args.kw_defaults:
            if kw_default is not None:
                _walk_for_refs(kw_default, refs)
        if func.returns is not None:
            _walk_for_refs(func.returns, refs)
        return

    if isinstance(node, ast.ClassDef) is True:
        class_def = cast(ast.ClassDef, node)
        for decorator in class_def.decorator_list:
            _walk_for_refs(decorator, refs)
        for base in class_def.bases:
            _walk_for_refs(base, refs)
        for keyword in class_def.keywords:
            _walk_for_refs(keyword.value, refs)
        return

    if isinstance(node, ast.Lambda) is True:
        lambda_node = cast(ast.Lambda, node)
        for default in lambda_node.args.defaults:
            _walk_for_refs(default, refs)
        for kw_default in lambda_node.args.kw_defaults:
            if kw_default is not None:
                _walk_for_refs(kw_default, refs)
        return

    for child in ast.iter_child_nodes(node):
        _walk_for_refs(child, refs)
