"""Assertion harness that turns the fixture files into real, failing tests.

The ``tests/test_*.py`` files are *fixtures*: real Python source whose lines are
annotated with inline expectation markers describing what ``explicit`` should
flag. This module reads those markers, runs the analyzer over each fixture, and
asserts that the set of checks produced matches the markers exactly — both that
expected checks fire (no regressions) and that nothing else does (no false
positives).

It is deliberately *not* named ``test_*.py``: ``python_files = check_*.py`` in
``pyproject.toml`` makes pytest collect only this file, so the fixtures are never
imported (importing them would execute their top-level calls to undefined
helpers and crash). The harness only ever reads them as text and parses them via
``analyze_file`` (which ``ast.parse``s — it does not import).

Marker grammar
--------------
Per-line expectation, written as a trailing comment on the line where the check
is reported (the construct's starting line):

    if value:                      # expect: if
    assert value and other         # expect: assert, assert, bool_op, bool_op

* The spec is a comma-separated list of check-type names (see ``CheckType``).
* Repeat a name to assert it is reported that many times on the line (a single
  line can legitimately produce several checks, e.g. one per boolean operand).
* A line with no ``expect`` marker must produce *zero* checks in every mode.

Modes
-----
A few checks (``lambda``, ``match_guard``) have a stricter opt-in variant enabled
via ``--include-extra``. A fixture exercising those declares, in a header comment
within its first lines:

    # explicit-test: modes=default,extra; extra=lambda

``modes`` lists the analyzer configurations to run (``default`` = no extras,
``extra`` = all listed extras enabled). Absent header => ``modes=default`` with no
extras. Per-item mode qualifiers restrict an expectation to one mode:

    case _ if count and value:     # expect: bool_op, bool_op, match_guard@default, match_guard@default, match_guard@extra

Here ``bool_op`` is expected in both modes, ``match_guard`` twice in default mode
(one per implicit operand) and once in extra mode (the whole guard).
"""

import re
from collections import Counter
from pathlib import Path

import pytest

from explicit.constructs import CheckType
from explicit.file_handlers import analyze_file


FIXTURES_DIR = Path(__file__).parent
VALID_MODES = frozenset({"default", "extra"})
VALID_CHECK_TYPES = frozenset(check_type.value for check_type in CheckType)

HEADER_RE = re.compile(r"#\s*explicit-test:\s*(?P<body>.*)$")
EXPECT_RE = re.compile(r"#\s*expect:\s*(?P<spec>.*?)\s*$")


class FixtureSpec:
    """Parsed expectations for one fixture file."""

    def __init__(self, path: Path):
        self.path = path
        self.modes: list[str] = ["default"]
        self.extras: set[str] = set()
        # mode -> Counter of (line_number, check_type) -> expected count
        self.expected: dict[str, Counter[tuple[int, str]]] = dict()
        self._parse()

    def _parse(self) -> None:
        lines = self.path.read_text(encoding="utf-8").splitlines()

        # Header directive (search the first handful of lines).
        for raw in lines[:10]:
            header_match = HEADER_RE.search(raw)
            if header_match is not None:
                self._parse_header(header_match.group("body"))
                break

        for mode in self.modes:
            self.expected[mode] = Counter()

        # Per-line expectation markers.
        for line_number, raw in enumerate(lines, start=1):
            expect_match = EXPECT_RE.search(raw)
            if expect_match is None:
                continue
            self._parse_expectation(line_number, expect_match.group("spec"))

    def _parse_header(self, body: str) -> None:
        for clause in body.split(";"):
            clause = clause.strip()
            if clause == "":
                continue
            key, _, value = clause.partition("=")
            key = key.strip()
            items = [item.strip() for item in value.split(",") if item.strip() != ""]
            if key == "modes":
                self.modes = items
            elif key == "extra":
                self.extras = set(items)
            else:
                raise ValueError(f"{self.path.name}: unknown header key {key!r}")

        for mode in self.modes:
            if mode not in VALID_MODES:
                raise ValueError(f"{self.path.name}: unknown mode {mode!r}")
        for extra in self.extras:
            if extra not in VALID_CHECK_TYPES:
                raise ValueError(f"{self.path.name}: unknown extra check {extra!r}")

    def _parse_expectation(self, line_number: int, spec: str) -> None:
        for item in spec.split(","):
            item = item.strip()
            if item == "":
                continue
            name, _, item_mode = item.partition("@")
            name = name.strip()
            item_mode = item_mode.strip()

            if name not in VALID_CHECK_TYPES:
                raise ValueError(
                    f"{self.path.name}:{line_number}: unknown check type {name!r}"
                )
            if item_mode != "" and item_mode not in self.modes:
                raise ValueError(
                    f"{self.path.name}:{line_number}: marker mode {item_mode!r} "
                    f"not in fixture modes {self.modes}"
                )

            target_modes = [item_mode] if item_mode != "" else self.modes
            for mode in target_modes:
                self.expected[mode][(line_number, name)] += 1

    def include_extra_for(self, mode: str) -> set[str] | None:
        if mode == "extra":
            return set(self.extras)
        return None

    def actual_for(self, mode: str) -> Counter[tuple[int, str]]:
        checks = analyze_file(
            self.path,
            include_extra=self.include_extra_for(mode),
        )
        return Counter((check.line, check.check_type.value) for check in checks)


def _discover_fixtures() -> list[Path]:
    fixtures = sorted(FIXTURES_DIR.glob("test_*.py"))
    if len(fixtures) == 0:
        raise RuntimeError(f"no fixtures found in {FIXTURES_DIR}")
    return fixtures


def _build_cases() -> list[tuple[Path, str]]:
    cases: list[tuple[Path, str]] = list()
    for path in _discover_fixtures():
        spec = FixtureSpec(path)
        for mode in spec.modes:
            cases.append((path, mode))
    return cases


def _case_id(case: tuple[Path, str]) -> str:
    path, mode = case
    return f"{path.stem}[{mode}]"


def _format_diff(
    expected: Counter[tuple[int, str]],
    actual: Counter[tuple[int, str]],
) -> str:
    missing = expected - actual
    unexpected = actual - expected
    lines: list[str] = list()
    if len(missing) > 0:
        lines.append("  expected but NOT reported:")
        for (line, check_type), count in sorted(missing.items()):
            lines.append(f"    line {line}: {check_type} x{count}")
    if len(unexpected) > 0:
        lines.append("  reported but NOT expected:")
        for (line, check_type), count in sorted(unexpected.items()):
            lines.append(f"    line {line}: {check_type} x{count}")
    return "\n".join(lines)


@pytest.mark.parametrize("case", _build_cases(), ids=_case_id)
def test_fixture(case: tuple[Path, str]) -> None:
    path, mode = case
    spec = FixtureSpec(path)
    expected = spec.expected[mode]
    actual = spec.actual_for(mode)
    if expected != actual:
        diff = _format_diff(expected, actual)
        pytest.fail(
            f"\n{path.name} [{mode}] mismatch between markers and analyzer:\n{diff}",
            pytrace=False,
        )
