"""Render violations as SARIF 2.1.0 for GitHub Code Scanning."""

from __future__ import annotations

from typing import Any

from .models import Severity, Violation

__all__ = ["SARIF_VERSION", "SARIF_SCHEMA", "to_sarif", "rule_description", "write_sarif"]

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
)

#: Fallback help text per code. ``validate`` keeps messages specific to the response;
#: SARIF rules have to be static, so each rule carries the class of problem instead.
_RULE_HELP = {
    "MCPR001": "Response is missing a field the schema declares as required.",
    "MCPR002": "Response contains a field the schema does not declare.",
    "MCPR003": "Response field has a different JSON type than the schema declares.",
    "MCPR004": "Response shape differs from the recorded baseline for this tool.",
    "MCPR005": "Error response does not match the error schema the server declared.",
}

_LEVEL = {Severity.HIGH: "error", Severity.MEDIUM: "warning", Severity.LOW: "note"}


def rule_description(code: str) -> str:
    """One-line description for a detector code."""
    return _RULE_HELP.get(code, "Response deviates from the declared schema.")


def to_sarif(violations: list[Violation]) -> dict[str, Any]:
    """Build a SARIF 2.1.0 log with one rule per distinct detector code."""
    rules = [
        {
            "id": code,
            "name": code,
            "shortDescription": {"text": rule_description(code)},
            "fullDescription": {"text": rule_description(code)},
            "defaultConfiguration": {"level": _LEVEL[_worst_severity(code, violations)]},
            "properties": {"tags": ["mcp", "schema-drift"]},
        }
        for code in sorted({v.code for v in violations})
    ]

    results = [
        {
            "ruleId": violation.code,
            "level": _LEVEL[violation.severity],
            "message": {"text": str(violation)},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": _uri_for(violation)},
                        "region": {"startLine": 1},
                    }
                }
            ],
            "properties": {"path": violation.path, "tool": violation.tool},
        }
        for violation in violations
    ]

    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "mcp-response-guard",
                        "informationUri": "https://github.com/yunaremaia/mcp-response-guard",
                        "rules": rules,
                    }
                },
                "results": results,
            }
        ],
    }


def _worst_severity(code: str, violations: list[Violation]) -> Severity:
    order = [Severity.HIGH, Severity.MEDIUM, Severity.LOW]
    present = {v.severity for v in violations if v.code == code}
    return min(present, key=order.index)


def _uri_for(violation: Violation) -> str:
    """SARIF locations must point at a file; fall back to a per-tool pseudo-URI.

    Violations come from live responses, not source files, so there is no real
    path to report. Keeping a stable, descriptive URI is more useful to a
    Code Scanning reader than dropping the location entirely.
    """
    return f"mcp-response://{violation.tool or 'tool'}"


def write_sarif(violations: list[Violation], path) -> None:
    import json
    from pathlib import Path

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(to_sarif(violations), indent=2) + "\n", encoding="utf-8")
