"""Data types shared across the package."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = ["Severity", "Violation"]


class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True)
class Violation:
    """One thing wrong with one response.

    ``path`` is a dotted/bracketed pointer into the response (``items[0].name``),
    or ``""`` when the problem is the response as a whole.
    """

    code: str
    severity: Severity
    message: str
    path: str = ""
    tool: str | None = None

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "path": self.path,
            "tool": self.tool,
        }

    def __str__(self) -> str:
        where = f" at {self.path}" if self.path else ""
        return f"[{self.code}] {self.severity.value}{where}: {self.message}"
