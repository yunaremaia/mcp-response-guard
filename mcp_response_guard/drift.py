"""Response shape fingerprints and drift comparison against a baseline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Severity, Violation

__all__ = [
    "DRIFT_CODE",
    "DRIFT_SEVERITY",
    "TYPE_CHANGED_SEVERITY",
    "compare_shapes",
    "shape_of",
    "DriftTracker",
]

DRIFT_CODE = "MCPR004"
DRIFT_SEVERITY = Severity.LOW
#: A field that changed type breaks consumers harder than one that merely appeared.
TYPE_CHANGED_SEVERITY = Severity.MEDIUM


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    # bool before int: bool is a subclass of int in Python, and JSON `true` is not a number.
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def shape_of(
    instance: Any, _prefix: str = "", _out: dict[str, str] | None = None
) -> dict[str, str]:
    """Flatten a response into ``{path: type}``.

    Arrays are represented by their first element: item shape, not item count.
    """
    out = {} if _out is None else _out
    path = _prefix or "$"
    out[path] = _type_name(instance)
    if isinstance(instance, dict):
        for key, value in instance.items():
            child = f"{path}.{key}"
            shape_of(value, child, out)
    elif isinstance(instance, list) and instance:
        shape_of(instance[0], f"{path}[]", out)
    return out


def compare_shapes(
    baseline: dict[str, str], current: dict[str, str], tool: str | None = None
) -> list[Violation]:
    """Report shape differences between a stored baseline and the latest response."""
    violations: list[Violation] = []
    for path in sorted(set(baseline) - set(current)):
        violations.append(
            Violation(
                code=DRIFT_CODE,
                severity=DRIFT_SEVERITY,
                message=f"field in baseline ({baseline[path]}) but absent from this response",
                path=path,
                tool=tool,
            )
        )
    for path in sorted(set(current) - set(baseline)):
        violations.append(
            Violation(
                code=DRIFT_CODE,
                severity=DRIFT_SEVERITY,
                message=f"field not in baseline but present in this response ({current[path]})",
                path=path,
                tool=tool,
            )
        )
    for path in sorted(set(baseline) & set(current)):
        if baseline[path] != current[path]:
            violations.append(
                Violation(
                    code=DRIFT_CODE,
                    severity=TYPE_CHANGED_SEVERITY,
                    message=f"type changed from {baseline[path]} to {current[path]}",
                    path=path,
                    tool=tool,
                )
            )
    return violations


class DriftTracker:
    """Per-tool shape baselines, persisted as one JSON file.

    The store maps tool name -> ``{path: type}``. An empty store means "no
    baseline yet": the first ``record`` for a tool just writes the baseline and
    reports no drift.
    """

    def __init__(self, store: str | Path | None = None) -> None:
        self.store = Path(store) if store is not None else None
        self.baselines: dict[str, dict[str, str]] = {}
        if self.store is not None and self.store.is_file():
            try:
                loaded = json.loads(self.store.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise ValueError(
                    f"baseline store {self.store} is not readable JSON: {exc}"
                ) from exc
            if not isinstance(loaded, dict):
                raise ValueError(f"baseline store {self.store} must contain a JSON object")
            self.baselines = {str(k): v for k, v in loaded.items() if isinstance(v, dict)}

    def baseline(self, tool: str) -> dict[str, str] | None:
        return self.baselines.get(tool)

    def check(self, tool: str, response: Any) -> list[Violation]:
        """Compare against the stored baseline without touching it."""
        baseline = self.baselines.get(tool)
        if baseline is None:
            return []
        return compare_shapes(baseline, shape_of(response), tool=tool)

    def record(self, tool: str, response: Any) -> list[Violation]:
        """Compare against the stored baseline, then replace it with this response."""
        violations = self.check(tool, response)
        self.baselines[tool] = shape_of(response)
        self.save()
        return violations

    def save(self) -> None:
        if self.store is None:
            return
        self.store.parent.mkdir(parents=True, exist_ok=True)
        self.store.write_text(
            json.dumps(self.baselines, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
