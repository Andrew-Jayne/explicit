import ast

from explicit.constructs import CheckType, StyleCheck


MAX_CODE_LENGTH = 100
EXCLUDED_NAMES = {"_"}


def find_single_use(
    tree: ast.Module, filename: str
) -> list[StyleCheck]:
    results: list[StyleCheck] = list()
    _analyze_scope(tree.body, filename, results)
    return results


def _is_dunder(name: str) -> bool:
    return len(name) > 4 and name.startswith("__") and name.endswith("__")


def _analyze_scope(
    body: list[ast.stmt],
    filename: str,
    results: list[StyleCheck],
    *,
    is_class: bool = False,
) -> None:
    _recurse_into_nested_scopes(body, filename, results)

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

    for name, positions in var_defs.items():
        if name in EXCLUDED_NAMES or name in excluded or _is_dunder(name) is True:
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
) -> None:
    for stmt in body:
        _find_nested_scopes(stmt, filename, results)


def _find_nested_scopes(
    node: ast.AST,
    filename: str,
    results: list[StyleCheck],
) -> None:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        _analyze_scope(node.body, filename, results)
        return
    if isinstance(node, ast.ClassDef):
        _analyze_scope(node.body, filename, results, is_class=True)
        return
    for child in ast.iter_child_nodes(node):
        _find_nested_scopes(child, filename, results)


def _walk_for_var_defs(
    node: ast.AST,
    var_defs: dict[str, list[tuple[int, int]]],
) -> None:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_defs.setdefault(target.id, list()).append(
                    (target.lineno, target.col_offset)
                )
    elif isinstance(node, ast.AnnAssign):
        if isinstance(node.target, ast.Name) and node.value is not None:
            var_defs.setdefault(node.target.id, list()).append(
                (node.target.lineno, node.target.col_offset)
            )

    if isinstance(
        node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
    ):
        return

    for child in ast.iter_child_nodes(node):
        _walk_for_var_defs(child, var_defs)


def _walk_for_func_defs(
    node: ast.AST,
    func_defs: dict[str, list[tuple[int, int, bool]]],
) -> None:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        has_decorator = len(node.decorator_list) > 0
        func_defs.setdefault(node.name, list()).append(
            (node.lineno, node.col_offset, has_decorator)
        )
        return

    if isinstance(node, (ast.ClassDef, ast.Lambda)):
        return

    for child in ast.iter_child_nodes(node):
        _walk_for_func_defs(child, func_defs)


def _walk_for_excluded(node: ast.AST, excluded: set[str]) -> None:
    if isinstance(node, ast.Global):
        excluded.update(node.names)
    elif isinstance(node, ast.Nonlocal):
        excluded.update(node.names)

    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        _collect_nonlocals_from_nested(node, excluded)
        return

    if isinstance(node, (ast.ClassDef, ast.Lambda)):
        return

    for child in ast.iter_child_nodes(node):
        _walk_for_excluded(child, excluded)


def _collect_nonlocals_from_nested(node: ast.AST, excluded: set[str]) -> None:
    for child in ast.iter_child_nodes(node):
        if isinstance(
            child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ):
            continue
        if isinstance(child, ast.Nonlocal):
            excluded.update(child.names)
        _collect_nonlocals_from_nested(child, excluded)


def _walk_for_refs(node: ast.AST, refs: dict[str, int]) -> None:
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
        refs[node.id] = refs.get(node.id, 0) + 1

    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for decorator in node.decorator_list:
            _walk_for_refs(decorator, refs)
        for default in node.args.defaults:
            _walk_for_refs(default, refs)
        for default in node.args.kw_defaults:
            if default is not None:
                _walk_for_refs(default, refs)
        if node.returns is not None:
            _walk_for_refs(node.returns, refs)
        return

    if isinstance(node, ast.ClassDef):
        for decorator in node.decorator_list:
            _walk_for_refs(decorator, refs)
        for base in node.bases:
            _walk_for_refs(base, refs)
        for keyword in node.keywords:
            _walk_for_refs(keyword.value, refs)
        return

    if isinstance(node, ast.Lambda):
        for default in node.args.defaults:
            _walk_for_refs(default, refs)
        for default in node.args.kw_defaults:
            if default is not None:
                _walk_for_refs(default, refs)
        return

    for child in ast.iter_child_nodes(node):
        _walk_for_refs(child, refs)
