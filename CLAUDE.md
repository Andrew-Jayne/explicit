# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`explicit` is a static analyzer (linter) for Python that flags constructs where the author's intent is ambiguous — implicit truthiness, ternaries, comprehensions, lambdas, single-letter/single-use names, etc. See [README.md](README.md) for the full catalog of checks and the philosophy behind them.

Targets **Python 3.14** (`requires-python = ">=3.14"`); it parses and reasons about 3.14 syntax.

## Commands

```bash
# Run the tool (the .venv is the project env; prefer uv)
uv run explicit <path>              # analyze a file or directory
uv run explicit . --format json     # json / csv / text output
uv run explicit . --stats-only
uv run explicit . --include-extra lambda --include-extra match_guard  # strict mode

# Test (assertion harness — see "Tests" below)
uv run pytest                       # runs tests/check_fixtures.py against every fixture

# Lint / format / typecheck
uv run ruff format .
uv run ruff check .                 # only isort import rules are enabled (select = ["I"])
uv run pyright                      # tests/ is excluded from type checking
```

If you see a `VIRTUAL_ENV does not match` warning from uv, it's harmless — uv uses `.venv`.

## Tests

`tests/test_*.py` are **fixture files, not pytest tests** — real Python source annotated with inline expectation markers. The assertion harness lives in **[tests/check_fixtures.py](tests/check_fixtures.py)**: it reads the markers, runs `analyze_file()` over each fixture, and asserts the multiset of `(line, check_type)` checks matches the markers exactly — catching both regressions (a check stops firing) and false positives (something new fires). Run it with:

```bash
uv run pytest                       # all fixtures, all modes
uv run pytest -k test_if            # one fixture
```

`pyproject.toml` sets `python_files = ["check_*.py"]` so pytest collects **only** the harness — the fixture `test_*.py` files are never imported (importing them would execute their top-level calls to undefined helpers and crash); the harness only `ast.parse`s them via `analyze_file`.

**Marker grammar** (full spec in the `check_fixtures.py` module docstring):
- Trailing comment on the line a check is reported on: `if value:  # expect: if`
- Repeat a type for multiplicity: `assert a and b  # expect: assert, assert, bool_op, bool_op`
- A line with no marker must produce **zero** checks.
- Strict `--include-extra` checks: a fixture declares modes in a header comment, e.g. `# explicit-test: modes=default,extra; extra=lambda`, and per-item mode qualifiers restrict an expectation: `lambda@extra` (only when extras on), `match_guard@default`, etc.
- The harness asserts type + count per line, **not** column (column is an implementation detail).

Each fixture maps to one check (`test_if.py`, `test_lambda.py`, `test_single_use_var.py`, …). `tests/OLD_TESTS/` is stale and not maintained. When you add or change a check, update the matching fixture's markers in the same change and run `uv run pytest`.

## Architecture

The flow is a straight pipeline; entry point is `explicit:main` (`pyproject.toml` script):

1. **[explicit/cli_args.py](explicit/cli_args.py)** — argparse with a typed `Args` namespace. Adding a flag means adding it both as a class attribute on `Args` and as an `add_argument` call. Flag-backed fields default to `None` ("not specified") so config-file values can fill them in; use `default=None` on `store_true` actions.
2. **[explicit/config.py](explicit/config.py)** — loads a `[tool.explicit]` table from `pyproject.toml` (discovered by walking up from the analyzed path, or via `--config`) using stdlib `tomllib`. Also reads `[project.scripts]`/`[project.gui-scripts]` to collect entry-point function names. Every flag field is `None` when unset.
3. **[explicit/main.py](explicit/main.py)** — resolves the path, loads config and merges it with CLI args (**CLI wins**, `--exclude-type` from both is merged), walks `*.py` (skipping `__pycache__`, `.venv`, etc.), runs analysis, applies `--exclude-type` filtering, dispatches to a reporter, and exits non-zero when any check is found (so it works as a CI gate). The flag-resolution helpers (`_resolve_bool`/`_resolve_format`/`_resolve_exclude_type`) implement the CLI-over-config precedence.
4. **[explicit/file_handlers.py](explicit/file_handlers.py)** — `analyze_file()` parses one file to an AST and runs the two analysis passes; entry-point names from config are threaded through to the single-use pass.
5. Analysis passes, both producing `StyleCheck` records:
   - **[explicit/code_visitor.py](explicit/code_visitor.py)** — `NodeVisitor` handles **expression/statement-level** checks (if/while/assert truthiness, ternary, bool-ops, comprehensions, lambda, `filter(None, …)`, match guards, single-letter vars) by walking AST nodes.
   - **[explicit/single_use.py](explicit/single_use.py)** — handles **scope-level** checks (single-use variables and single-use functions). This needs a two-pass, scope-aware analysis (collect definitions, count references, then flag) — that's why it's separate from the node visitor. Exemptions live here: `ALL_CAPS` constants are never flagged as single-use vars; `main`, names referenced only inside an `if __name__ == "__main__":` guard (`_collect_main_guard_names`), and `[project.scripts]` entry points are never flagged as single-use funcs.
6. **[explicit/reporters.py](explicit/reporters.py)** — formats the collected `StyleCheck`s into text / json / csv.

**Central types** live in [explicit/constructs.py](explicit/constructs.py): `CheckType` (the `StrEnum` registry of every check — its members are also the valid `--exclude-type` values), `StyleCheck` (the `NamedTuple` every check produces: file, line, column, code, context, check_type), `ReportFormat`, and `Colors`. Adding a new check almost always starts by adding a `CheckType` member here.

## Code style convention (important)

The source is written in the verbose, explicit style the tool enforces. Match it when editing:

- Explicit comparisons, never truthiness: `if args.no_color is True:`, `if len(files) == 0:`, `if should_skip is False:` — not `if args.no_color:` or `if not files:`.
- `list()` / `dict()` / `set()` instead of `[]` / `{}` literals for empty constructors.
- No comprehensions, ternaries, or lambdas in the tool's own source — use explicit `for` loops and named functions.

Two consequences of the `is True` style worth knowing:

- **It defeats pyright's type narrowing.** `if isinstance(node, ast.Assign) is True:` does *not* narrow `node`, so accessing `node.targets` afterward errors. The established fix (see `code_visitor.py` / `single_use.py`) is `cast(ast.Assign, node).targets` from `typing.cast`. Keep `uv run pyright explicit/` at zero errors.
- **The codebase does not fully pass its own linter.** Running `uv run explicit explicit/` reports dozens of violations (single-use locals, etc.) — dogfooding is aspirational, not enforced. Don't contort readable code just to drive that count to zero; match the standard of the surrounding code.
