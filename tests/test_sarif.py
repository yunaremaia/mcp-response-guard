"""SARIF 2.1.0 output shape."""

from __future__ import annotations

from mcp_response_guard import Severity, Violation, to_sarif, write_sarif
from mcp_response_guard.sarif import rule_description

VIOLATIONS = [
    Violation(
        code="MCPR001", severity=Severity.HIGH, message="missing size", path="size", tool="fs.read"
    ),
    Violation(
        code="MCPR003", severity=Severity.MEDIUM, message="wrong type", path="size", tool="fs.read"
    ),
]


def test_log_declares_sarif_2_1_0():
    log = to_sarif(VIOLATIONS)
    assert log["version"] == "2.1.0"
    assert log["$schema"].endswith("sarif-schema-2.1.0.json")


def test_one_result_per_violation():
    assert len(to_sarif(VIOLATIONS)["runs"][0]["results"]) == 2


def test_one_rule_per_distinct_code():
    rules = to_sarif(VIOLATIONS)["runs"][0]["tool"]["driver"]["rules"]
    assert sorted(r["id"] for r in rules) == ["MCPR001", "MCPR003"]


def test_rule_level_reflects_the_worst_violation_of_that_code():
    rules = {r["id"]: r for r in to_sarif(VIOLATIONS)["runs"][0]["tool"]["driver"]["rules"]}
    assert rules["MCPR001"]["defaultConfiguration"]["level"] == "error"
    assert rules["MCPR003"]["defaultConfiguration"]["level"] == "warning"


def test_result_level_follows_each_violation_severity():
    results = to_sarif(VIOLATIONS)["runs"][0]["results"]
    assert [r["level"] for r in results] == ["error", "warning"]


def test_result_carries_a_location_uri_per_tool():
    result = to_sarif(VIOLATIONS)["runs"][0]["results"][0]
    uri = result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
    assert uri == "mcp-response://fs.read"


def test_every_detector_code_has_a_description():
    for code in ("MCPR001", "MCPR002", "MCPR003", "MCPR004", "MCPR005"):
        assert rule_description(code).endswith(".")


def test_clean_run_has_no_results_and_no_rules():
    run = to_sarif([])["runs"][0]
    assert run["results"] == []
    assert run["tool"]["driver"]["rules"] == []


def test_write_sarif_creates_parent_dirs(tmp_path):
    target = tmp_path / "out" / "results.sarif"
    write_sarif(VIOLATIONS, target)
    assert '"2.1.0"' in target.read_text()
