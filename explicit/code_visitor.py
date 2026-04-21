import ast
from collections.abc import Generator
from typing import cast

from explicit.constructs import CheckType, StyleCheck


MAX_CODE_LENGTH = 100
MIN_FILTER_ARGS = 2

CompNode = ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp

_COMP_LABELS: dict[CheckType, str] = {
    CheckType.LIST_COMP: "List comprehension",
    CheckType.SET_COMP: "Set comprehension",
    CheckType.DICT_COMP: "Dict comprehension",
}

_CONTEXT_TEMPLATES: dict[CheckType, str] = {
    CheckType.IF: "if {}:",
    CheckType.WHILE: "while {}:",
    CheckType.ASSERT: "assert {}",
    CheckType.TERNARY: "... if {} else ...",
    CheckType.MATCH_GUARD: "match case guard: ... if {}",
    CheckType.LAMBDA: "lambda: ... if {} else ...",
}


class NodeVisitor:
    filename: str
    seen_names: set[str]
    disallow_lambda: bool
    disallow_logic_in_match: bool

    def __init__(
        self,
        filename: str,
        *,
        disallow_lambda: bool = False,
        disallow_logic_in_match: bool = False,
    ) -> None:
        self.filename = filename
        self.disallow_lambda = disallow_lambda
        self.disallow_logic_in_match = disallow_logic_in_match
        self.seen_names = set()

    def visit(self, node: ast.AST) -> Generator[StyleCheck]:
        method = f"visit_{type(node).__name__}"
        yield from getattr(self, method, self.generic_visit)(node)

    def generic_visit(self, node: ast.AST) -> Generator[StyleCheck]:
        for child in ast.iter_child_nodes(node):
            yield from self.visit(child)

    def visit_If(self, node: ast.If) -> Generator[StyleCheck]:
        if isinstance(node.test, ast.Name) is False:
            yield from self._implicit_bool_check(node.test, CheckType.IF)
        yield from self.generic_visit(node)

    def visit_While(self, node: ast.While) -> Generator[StyleCheck]:
        yield from self._implicit_bool_check(node.test, CheckType.WHILE)
        yield from self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> Generator[StyleCheck]:
        yield from self._implicit_bool_check(node.test, CheckType.ASSERT)
        yield from self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> Generator[StyleCheck]:
        unparsed = ast.unparse(node)
        code = unparsed[:MAX_CODE_LENGTH] + (
            "..." if len(unparsed) > MAX_CODE_LENGTH else ""
        )
        yield StyleCheck(
            file=self.filename,
            line=node.lineno,
            column=node.col_offset,
            code=code,
            context="Ternary expression - use explicit if/else block instead",
            check_type=CheckType.TERNARY,
        )
        yield from self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> Generator[StyleCheck]:
        op_str = "and" if isinstance(node.op, ast.And) is True else "or"
        for value in node.values:
            yield from self._implicit_bool_check(
                value, CheckType.BOOL_OP, f"... {op_str} {ast.unparse(value)} ..."
            )
        yield from self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp) -> Generator[StyleCheck]:
        yield from self._visit_comp_node(node, CheckType.LIST_COMP)

    def visit_SetComp(self, node: ast.SetComp) -> Generator[StyleCheck]:
        yield from self._visit_comp_node(node, CheckType.SET_COMP)

    def visit_DictComp(self, node: ast.DictComp) -> Generator[StyleCheck]:
        yield from self._visit_comp_node(node, CheckType.DICT_COMP)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> Generator[StyleCheck]:
        unparsed = ast.unparse(node)
        code = unparsed[:MAX_CODE_LENGTH] + (
            "..." if len(unparsed) > MAX_CODE_LENGTH else ""
        )
        yield StyleCheck(
            file=self.filename,
            line=node.lineno,
            column=node.col_offset,
            code=code,
            context="Generator expression - use explicit for loop/generator function",
            check_type=CheckType.GENERATOR,
        )
        yield from self._visit_comprehension_filters(node, "generator expression")
        yield from self.generic_visit(node)

    def visit_Lambda(self, node: ast.Lambda) -> Generator[StyleCheck]:
        if self.disallow_lambda is True:
            unparsed = ast.unparse(node)
            code = unparsed[:MAX_CODE_LENGTH] + (
                "..." if len(unparsed) > MAX_CODE_LENGTH else ""
            )
            yield StyleCheck(
                file=self.filename,
                line=node.lineno,
                column=node.col_offset,
                code=code,
                context="Lambda expression - use named function instead (--disallow-lambda enabled)",
                check_type=CheckType.LAMBDA,
            )
        elif isinstance(node.body, ast.IfExp) is True:
            ifexp_body = cast(ast.IfExp, node.body)
            yield from self._implicit_bool_check(ifexp_body.test, CheckType.LAMBDA)
        else:
            body_implicit = False
            if isinstance(node.body, ast.BoolOp) is True:
                body_implicit = True
            elif isinstance(node.body, ast.UnaryOp) is True:
                unaryop_body = cast(ast.UnaryOp, node.body)
                if isinstance(unaryop_body.op, ast.Not) is True:
                    body_implicit = True
            if body_implicit is True:
                yield StyleCheck(
                    file=self.filename,
                    line=node.lineno,
                    column=node.col_offset,
                    code=f"lambda ...: {ast.unparse(node.body)}",
                    context=f"lambda with implicit boolean: lambda ...: {ast.unparse(node.body)}",
                    check_type=CheckType.LAMBDA,
                )
        yield from self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> Generator[StyleCheck]:
        for case in node.cases:
            if case.guard is not None:
                if self.disallow_logic_in_match is True:
                    yield StyleCheck(
                        file=self.filename,
                        line=getattr(case.guard, "lineno", node.lineno),
                        column=getattr(case.guard, "col_offset", node.col_offset),
                        code=f"case ... if {ast.unparse(case.guard)}",
                        context="Match case with guard - move logic to case body (--disallow-logic-in-match enabled)",
                        check_type=CheckType.MATCH_GUARD,
                    )
                else:
                    yield from self._implicit_bool_check(
                        case.guard, CheckType.MATCH_GUARD
                    )
        yield from self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Generator[StyleCheck]:
        yield from self._check_single_letter_name(node, "use descriptive function name")
        all_args: list[ast.arg] = (
            node.args.args + node.args.kwonlyargs + node.args.posonlyargs
        )
        for arg in all_args:
            yield from self._check_single_letter_name(
                arg, "use descriptive parameter name"
            )
        yield from self.generic_visit(node)

    def visit_AsyncFunctionDef(
        self, node: ast.AsyncFunctionDef
    ) -> Generator[StyleCheck]:
        yield from self._check_single_letter_name(node, "use descriptive function name")
        all_args: list[ast.arg] = (
            node.args.args + node.args.kwonlyargs + node.args.posonlyargs
        )
        for arg in all_args:
            yield from self._check_single_letter_name(
                arg, "use descriptive parameter name"
            )
        yield from self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> Generator[StyleCheck]:
        yield from self._check_single_letter_name(node, "use descriptive class name")
        yield from self.generic_visit(node)

    def visit_For(self, node: ast.For) -> Generator[StyleCheck]:
        match node.target:
            case ast.Name():
                yield from self._check_single_letter_name(
                    node.target, "use descriptive loop variable (not 'i', 'j', 'k')"
                )
            case ast.Tuple():
                for elt in node.target.elts:
                    if isinstance(elt, ast.Name) is True:
                        name_elt = cast(ast.Name, elt)
                        yield from self._check_single_letter_name(
                            name_elt, "use descriptive loop variable"
                        )
            case _:
                pass
        yield from self.generic_visit(node)

    def visit_ExceptHandler(
        self, node: ast.ExceptHandler
    ) -> Generator[StyleCheck]:
        yield from self._check_single_letter_name(
            node, "use descriptive exception variable (not 'e')"
        )
        yield from self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> Generator[StyleCheck]:
        for target in node.targets:
            match target:
                case ast.Name():
                    yield from self._check_single_letter_name(
                        target, "use descriptive variable name"
                    )
                case ast.Tuple():
                    for elt in target.elts:
                        if isinstance(elt, ast.Name) is True:
                            name_elt = cast(ast.Name, elt)
                            yield from self._check_single_letter_name(
                                name_elt, "use descriptive variable name"
                            )
                case _:
                    pass
        yield from self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Generator[StyleCheck]:
        match node.target:
            case ast.Name():
                yield from self._check_single_letter_name(
                    node.target, "use descriptive variable name"
                )
            case _:
                pass
        yield from self.generic_visit(node)

    def visit_NamedExpr(
        self,
        node: ast.NamedExpr,
    ) -> Generator[StyleCheck]:
        yield from self._check_single_letter_name(
            node.target, "use descriptive variable name (walrus operator)"
        )
        yield from self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Generator[StyleCheck]:
        if isinstance(node.func, ast.Name) is True:
            func_node = cast(ast.Name, node.func)
            if func_node.id == "filter" and len(node.args) >= MIN_FILTER_ARGS:
                first_arg = node.args[0]
                if isinstance(first_arg, ast.Constant) is True:
                    const_arg = cast(ast.Constant, first_arg)
                    if const_arg.value is None:
                        yield StyleCheck(
                            file=self.filename,
                            line=node.lineno,
                            column=node.col_offset,
                            code="filter(None, ...)",
                            context="filter(None, ...) - implicit truthiness filter",
                            check_type=CheckType.FILTER,
                        )
        yield from self.generic_visit(node)

    def _implicit_bool_check(
        self,
        node: ast.expr,
        check_type: CheckType,
        context: str | None = None,
    ) -> Generator[StyleCheck]:
        match node:
            case ast.Compare():
                return
            case ast.Constant():
                if isinstance(node.value, bool) is True:
                    return
            case ast.BoolOp():
                for value in node.values:
                    yield from self._implicit_bool_check(value, check_type, context)
                return
            case ast.UnaryOp():
                if (
                    isinstance(node.op, ast.Not) is True
                    and isinstance(node.operand, ast.Compare) is True
                ):
                    return
            case _:
                pass
        if context is None:
            context = _CONTEXT_TEMPLATES[check_type].format(ast.unparse(node))
        yield StyleCheck(
            file=self.filename,
            line=node.lineno,
            column=node.col_offset,
            code=ast.unparse(node),
            context=context,
            check_type=check_type,
        )

    def _check_single_letter_name(
        self,
        node: ast.Name
        | ast.arg
        | ast.FunctionDef
        | ast.AsyncFunctionDef
        | ast.ClassDef
        | ast.ExceptHandler,
        context: str,
    ) -> Generator[StyleCheck]:
        match node:
            case ast.Name():
                name = node.id
            case ast.arg():
                name = node.arg
            case ast.ExceptHandler():
                if node.name is None:
                    return
                name = node.name
            case _:
                name = node.name
        if len(name) == 1 and name != "_":
            key = f"{name}:{node.lineno}:{node.col_offset}"
            if key not in self.seen_names:
                self.seen_names.add(key)
                yield StyleCheck(
                    file=self.filename,
                    line=node.lineno,
                    column=node.col_offset,
                    code=name,
                    context=f"Single-letter variable '{name}' - {context}",
                    check_type=CheckType.SINGLE_LETTER_VAR,
                )

    def _visit_comprehension_filters(
        self, node: CompNode, comp_name: str
    ) -> Generator[StyleCheck]:
        for gen_index, generator in enumerate(node.generators):
            for if_clause in generator.ifs:
                if len(node.generators) > 1:
                    context = f"nested {comp_name} (level {gen_index + 1}): ... if {ast.unparse(if_clause)}"
                else:
                    context = f"{comp_name}: ... if {ast.unparse(if_clause)}"
                yield from self._implicit_bool_check(
                    if_clause, CheckType.COMPREHENSION, context
                )

    def _visit_comp_node(
        self, node: CompNode, check_type: CheckType
    ) -> Generator[StyleCheck]:
        label = _COMP_LABELS[check_type]
        unparsed = ast.unparse(node)
        code = unparsed[:MAX_CODE_LENGTH] + (
            "..." if len(unparsed) > MAX_CODE_LENGTH else ""
        )
        yield StyleCheck(
            file=self.filename,
            line=node.lineno,
            column=node.col_offset,
            code=code,
            context=f"{label} - use explicit for loop instead",
            check_type=check_type,
        )
        yield from self._visit_comprehension_filters(node, label.lower())
        yield from self.generic_visit(node)
