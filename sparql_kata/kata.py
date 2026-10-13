"""Load and validate kata definitions from YAML files.

Validation is strict on purpose: unknown keys (typos like `order_sensitve`)
raise a KataError instead of being silently ignored. All file paths in a
kata are relative to the kata's own YAML file.

See README.md for the full format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .compare import COLUMN_MAPPINGS, POSITIONAL
from .hints import ALL_SYMPTOMS

ALLOWED_KEYS = {
    "id", "title", "prompt", "level", "concepts",
    "prefixes", "datasets", "reference", "reference_file",
    "grading", "hints",
}
ALLOWED_DATASET_KEYS = {"visible", "hidden"}
ALLOWED_GRADING_KEYS = {"order_sensitive", "column_mapping", "ignore_lang", "decimal_places"}


class KataError(Exception):
    """A problem with the kata definition itself (a teacher-side error)."""


@dataclass(frozen=True)
class Dataset:
    label: str   # "visible", "hidden-1", "hidden-2", ...
    path: Path
    hidden: bool


@dataclass(frozen=True)
class GradingOptions:
    order_sensitive: bool = False
    column_mapping: str = POSITIONAL
    ignore_lang: bool = False
    decimal_places: int = 6


@dataclass
class Kata:
    id: str
    title: str
    prompt: str
    reference: str                 # the reference SPARQL query text
    prefixes: dict[str, str]       # injected into every query (students can skip PREFIX lines)
    datasets: list[Dataset]        # visible dataset first, then hidden ones
    grading: GradingOptions = field(default_factory=GradingOptions)
    hints: dict = field(default_factory=dict)  # symptom code -> str or {lang: str}
    source_path: Path | None = None


def load_kata(path: str | Path) -> Kata:
    path = Path(path)
    if not path.is_file():
        raise KataError(f"Kata file not found: {path}")

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise KataError(f"Invalid YAML in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise KataError(f"{path}: expected a YAML mapping at the top level")

    _reject_unknown_keys(data, ALLOWED_KEYS, f"{path}")

    base_dir = path.parent
    kata_id = _require_str(data, "id", path)

    return Kata(
        id=kata_id,
        title=str(data.get("title", kata_id)),
        prompt=_require_str(data, "prompt", path),
        reference=_load_reference(data, base_dir, path),
        prefixes=_load_prefixes(data, path),
        datasets=_load_datasets(data, base_dir, path),
        grading=_load_grading(data, path),
        hints=_load_hints(data, path),
        source_path=path,
    )


# --- helpers -----------------------------------------------------------------

def _reject_unknown_keys(mapping: dict, allowed: set[str], where: str) -> None:
    unknown = set(mapping) - allowed
    if unknown:
        raise KataError(f"{where}: unknown key(s) {sorted(unknown)}. Allowed: {sorted(allowed)}")


def _require_str(data: dict, key: str, path: Path) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise KataError(f"{path}: '{key}' is required and must be a non-empty string")
    return value


def _load_reference(data: dict, base_dir: Path, path: Path) -> str:
    has_inline = "reference" in data
    has_file = "reference_file" in data
    if has_inline == has_file:
        raise KataError(f"{path}: give exactly one of 'reference' or 'reference_file'")

    if has_inline:
        return _require_str(data, "reference", path)

    reference_path = base_dir / str(data["reference_file"])
    if not reference_path.is_file():
        raise KataError(f"{path}: reference_file not found: {reference_path}")
    return reference_path.read_text(encoding="utf-8")


def _load_prefixes(data: dict, path: Path) -> dict[str, str]:
    prefixes = data.get("prefixes") or {}
    if not isinstance(prefixes, dict):
        raise KataError(f"{path}: 'prefixes' must be a mapping like {{ex: 'http://example.org/'}}")
    return {str(prefix): str(iri) for prefix, iri in prefixes.items()}


def _load_datasets(data: dict, base_dir: Path, path: Path) -> list[Dataset]:
    section = data.get("datasets")
    if not isinstance(section, dict):
        raise KataError(f"{path}: 'datasets' is required, with at least a 'visible' file")
    _reject_unknown_keys(section, ALLOWED_DATASET_KEYS, f"{path} datasets")

    if "visible" not in section:
        raise KataError(f"{path}: 'datasets.visible' is required")

    hidden = section.get("hidden") or []
    if isinstance(hidden, str):
        hidden = [hidden]

    datasets = [Dataset("visible", base_dir / str(section["visible"]), hidden=False)]
    for number, hidden_file in enumerate(hidden, start=1):
        datasets.append(Dataset(f"hidden-{number}", base_dir / str(hidden_file), hidden=True))

    for dataset in datasets:
        if not dataset.path.is_file():
            raise KataError(f"{path}: dataset file not found: {dataset.path}")
    return datasets


def _load_grading(data: dict, path: Path) -> GradingOptions:
    section = data.get("grading") or {}
    if not isinstance(section, dict):
        raise KataError(f"{path}: 'grading' must be a mapping")
    _reject_unknown_keys(section, ALLOWED_GRADING_KEYS, f"{path} grading")

    options = GradingOptions(**section)

    if not isinstance(options.order_sensitive, bool):
        raise KataError(f"{path}: grading.order_sensitive must be true or false")
    if not isinstance(options.ignore_lang, bool):
        raise KataError(f"{path}: grading.ignore_lang must be true or false")
    if options.column_mapping not in COLUMN_MAPPINGS:
        raise KataError(f"{path}: grading.column_mapping must be one of {COLUMN_MAPPINGS}")
    if not isinstance(options.decimal_places, int) or isinstance(options.decimal_places, bool) \
            or not 0 <= options.decimal_places <= 12:
        raise KataError(f"{path}: grading.decimal_places must be an integer between 0 and 12")
    return options


def _load_hints(data: dict, path: Path) -> dict:
    hints = data.get("hints") or {}
    if not isinstance(hints, dict):
        raise KataError(f"{path}: 'hints' must be a mapping of symptom code -> text")
    unknown = set(hints) - set(ALL_SYMPTOMS)
    if unknown:
        raise KataError(f"{path}: unknown hint code(s) {sorted(unknown)}. Valid codes: {sorted(ALL_SYMPTOMS)}")
    return hints
