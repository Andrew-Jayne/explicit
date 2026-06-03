import tomllib
from pathlib import Path
from typing import cast

from explicit.constructs import EXTRA_CHECKS, CheckType, ReportFormat


# Keys recognized under [tool.explicit] in pyproject.toml. TOML convention is
# hyphenated keys, but underscores are accepted too so they line up with the
# argparse destinations.
class Config:
    """Project configuration loaded from a pyproject.toml [tool.explicit] table.

    Every flag-backed field defaults to None, meaning "not specified" so the CLI
    layer can tell the difference between an explicit choice and a fallback.
    """

    format: ReportFormat | None
    exclude_type: list[str] | None
    include_extra: list[str] | None
    no_color: bool | None
    stats_only: bool | None
    entry_points: set[str]

    def __init__(self) -> None:
        self.format = None
        self.exclude_type = None
        self.include_extra = None
        self.no_color = None
        self.stats_only = None
        self.entry_points = set()


def find_pyproject(start: Path) -> Path | None:
    current = start.resolve()
    if current.is_file() is True:
        current = current.parent
    while True:
        candidate = current / "pyproject.toml"
        if candidate.is_file() is True:
            return candidate
        if current.parent == current:
            return None
        current = current.parent


def load_config(start: Path, config_path: Path | None = None) -> Config:
    config = Config()

    if config_path is not None:
        pyproject = config_path
    else:
        pyproject = find_pyproject(start)

    if pyproject is None:
        return config
    if pyproject.is_file() is False:
        return config

    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    _load_entry_points(data, config)
    _load_tool_table(data, config)
    return config


def _load_entry_points(data: dict[str, object], config: Config) -> None:
    project = data.get("project")
    if isinstance(project, dict) is False:
        return
    for group in ("scripts", "gui-scripts"):
        scripts = _as_table(project).get(group)
        if isinstance(scripts, dict) is False:
            continue
        for target in _as_table(scripts).values():
            if isinstance(target, str) is True:
                name = _callable_name(str(target))
                if name != "":
                    config.entry_points.add(name)


def _callable_name(target: str) -> str:
    # "package.module:func.attr" -> "func"
    if ":" not in target:
        return ""
    return target.split(":", 1)[1].split(".", 1)[0].strip()


def _load_tool_table(data: dict[str, object], config: Config) -> None:
    tool = data.get("tool")
    if isinstance(tool, dict) is False:
        return
    explicit = _as_table(tool).get("explicit")
    if isinstance(explicit, dict) is False:
        return
    table = _as_table(explicit)

    format_value = _lookup(table, "format")
    if isinstance(format_value, str) is True:
        config.format = ReportFormat(str(format_value))

    exclude_value = _lookup(table, "exclude-type")
    if isinstance(exclude_value, list) is True:
        config.exclude_type = _validate_against(
            cast(list[object], exclude_value), set(CheckType)
        )

    include_value = _lookup(table, "include-extra")
    if isinstance(include_value, list) is True:
        config.include_extra = _validate_against(
            cast(list[object], include_value), EXTRA_CHECKS
        )

    config.no_color = _lookup_bool(table, "no-color")
    config.stats_only = _lookup_bool(table, "stats-only")


def _validate_against(
    values: list[object], allowed: frozenset[CheckType] | set[CheckType]
) -> list[str]:
    valid: list[str] = list()
    for value in values:
        if isinstance(value, str) is True and str(value) in allowed:
            valid.append(str(value))
    return valid


def _lookup(table: dict[str, object], key: str) -> object:
    if key in table:
        return table[key]
    underscored = key.replace("-", "_")
    if underscored in table:
        return table[underscored]
    return None


def _lookup_bool(table: dict[str, object], key: str) -> bool | None:
    value = _lookup(table, key)
    if isinstance(value, bool) is True:
        return bool(value)
    return None


def _as_table(value: object) -> dict[str, object]:
    return cast(dict[str, object], value)
