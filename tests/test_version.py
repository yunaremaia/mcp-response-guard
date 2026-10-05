"""The published version must not drift between code and packaging metadata.

Two independent sources declare the version — ``mcp_response_guard.__version__``
and ``[project] version`` in pyproject.toml — and CI publishes a tag built from
one of them. A mismatch ships a package whose metadata disagrees with its own
`--version` output, so this is checked rather than trusted.
"""

from __future__ import annotations

import re
from pathlib import Path

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # Python 3.10 — the `tomli` backport is a dev dep
    import tomli as tomllib

from mcp_response_guard import __version__

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _pyproject_version() -> str:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]


def test_version_is_a_release_tag():
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__)


def test_pyproject_version_matches_code():
    assert _pyproject_version() == __version__
