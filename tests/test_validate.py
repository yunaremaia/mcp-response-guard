"""Validation of responses against declared schemas."""

from __future__ import annotations

import pytest
from jsonschema.exceptions import SchemaError

from mcp_response_guard import Severity, validate_error_response, validate_response

SCHEMA = {
    "type": "object",
    "properties": {
        "path": {"type": "string"},
        "size": {"type": "integer"},
        "content": {"type": "string"},
    },
    "required": ["path", "size"],
}


def test_matching_response_has_no_violations():
    response = {"path": "/etc/hosts", "size": 42, "content": "127.0.0.1 localhost"}
    assert validate_response(response, SCHEMA) == []


def test_missing_required_field_is_high_severity():
    response = {"content": "x"}
    codes = [(v.code, v.severity) for v in validate_response(response, SCHEMA)]
    assert codes == [("MCPR001", Severity.HIGH)]


def test_missing_required_field_names_only_absent_fields():
    response = {"path": "/etc/hosts"}
    violations = validate_response(response, SCHEMA)
    assert len(violations) == 1
    assert "size" in violations[0].message
    assert "path" not in violations[0].message


def test_type_mismatch_is_medium_severity():
    violations = validate_response({"path": "/etc/hosts", "size": "42"}, SCHEMA)
    assert [(v.code, v.severity) for v in violations] == [("MCPR003", Severity.MEDIUM)]
    assert violations[0].path == "size"


def test_undeclared_field_is_detected_even_when_additional_properties_is_not_false():
    response = {"path": "/etc/hosts", "size": 42, "encoding": "utf-8"}
    violations = validate_response(response, SCHEMA)
    assert [(v.code, v.path) for v in violations] == [("MCPR002", "encoding")]


def test_undeclared_nested_field_reports_its_full_path():
    schema = {
        "type": "object",
        "properties": {"meta": {"type": "object", "properties": {"id": {"type": "integer"}}}},
    }
    response = {"meta": {"id": 1, "nested": {"deep": True}}}
    violations = validate_response(response, schema)
    assert [(v.code, v.path) for v in violations] == [("MCPR002", "meta.nested")]


def test_boolean_is_not_accepted_as_integer():
    # bool subclasses int in Python; JSON Schema says they are different types.
    violations = validate_response({"path": "a", "size": True}, SCHEMA)
    assert [v.code for v in violations] == ["MCPR003"]


def test_free_form_object_is_not_flooded_with_extra_field_violations():
    # Only descends into subschemas the schema describes.
    schema = {"type": "object", "properties": {"items": {"type": "array"}}}
    violations = validate_response({"items": [{"a": 1}, {"b": 2}]}, schema)
    assert violations == []


def test_tool_name_is_recorded_on_violations():
    violations = validate_response({}, SCHEMA, tool="filesystem.read_file")
    assert violations[0].tool == "filesystem.read_file"


def test_invalid_schema_raises():
    with pytest.raises(SchemaError):
        validate_response({}, {"type": "not-a-type"})


def test_error_response_violations_are_tagged_mcpr005():
    violations = validate_error_response({"message": "boom"}, SCHEMA, tool="fs")
    assert {v.code for v in violations} == {"MCPR005"}
    assert "error response" in violations[0].message
    assert violations[0].tool == "fs"


def test_matching_error_response_is_clean():
    error_schema = {
        "type": "object",
        "properties": {"message": {"type": "string"}},
        "required": ["message"],
    }
    assert validate_error_response({"message": "boom"}, error_schema) == []
