"""Pydantic v2 Input-Validation für MCP Tool-Parameter.

Shell-Injection-Prevention: Blockiert gefährliche Zeichen in Freitext-Feldern.
"""

import re
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

# Regex für UUID-Matching (vollständig oder Prefix ≥8 Zeichen)
_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}(?:-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12})?$",
    re.IGNORECASE,
)

# Gefährliche Zeichen für Shell-Injection
_SHELL_INJECTION_CHARS = re.compile(r"[;&|$\\`{}]")

# Erlaubte Zeichen für Tags
_TAG_PATTERN = re.compile(r"^[\w\-\.]+$")

# Erlaubte Priority-Werte
_VALID_PRIORITIES = {"H", "M", "L"}

# Erlaubte Status-Werte für task_list
_VALID_STATUSES = {"pending", "completed", "deleted", "waiting", "recurring"}


def _check_uuid(value: str) -> str:
    """Validiert UUID-Format (vollständig oder Prefix >= 8 Zeichen, nur Hex und Bindestriche)."""
    if not _UUID_PATTERN.match(value):
        raise ValueError(
            f"Ungültiges UUID-Format: '{value}'. Nur Hex-Zeichen und Bindestriche erlaubt."
        )
    return value


def _check_shell_injection(value: str) -> str:
    """Blockiert Shell-Injection-Zeichen in Freitext-Feldern."""
    if _SHELL_INJECTION_CHARS.search(value):
        raise ValueError(
            "Ungültige Zeichen im Text. Folgende Zeichen sind nicht erlaubt: ; | & $ \\ ` { }"
        )
    return value


# Annotated-Typen für häufig verwendete Felder
UUIDStr = Annotated[
    str,
    Field(min_length=8, description="Task UUID (vollständig oder Prefix ≥8 Zeichen)"),
]

SafeStr = Annotated[
    str,
    Field(min_length=1, max_length=4096, description="Text ohne Shell-Sonderzeichen"),
]

TagStr = Annotated[
    str,
    Field(pattern=r"^[\w\-\.]+$", description="Tag-Name (nur Wörter, Bindestriche, Punkte)"),
]


class TaskAddInput(BaseModel):
    """Parameter für task_add."""

    description: str = Field(min_length=1, max_length=4096)
    project: str | None = Field(default=None, max_length=256)
    priority: str | None = Field(default=None)
    due: str | None = Field(default=None, max_length=64)
    scheduled: str | None = Field(default=None, max_length=64)
    wait: str | None = Field(default=None, max_length=64)
    recur: str | None = Field(default=None, max_length=64)
    tags: list[str] | None = Field(default=None)

    @field_validator("description", "project", "due", "scheduled", "wait", "recur", mode="before")
    @classmethod
    def no_shell_injection(cls, v: str | None) -> str | None:
        if v is not None:
            _check_shell_injection(v)
        return v

    @field_validator("priority")
    @classmethod
    def valid_priority(cls, v: str | None) -> str | None:
        if v is not None and v not in _VALID_PRIORITIES:
            raise ValueError(f"Priority muss H, M oder L sein, nicht '{v}'")
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def valid_tags(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            for tag in v:
                if not _TAG_PATTERN.match(tag):
                    raise ValueError(
                        f"Tag '{tag}' enthält ungültige Zeichen. Nur Wörter, Bindestriche und Punkte erlaubt."
                    )
        return v


class TaskModifyInput(BaseModel):
    """Parameter für task_modify."""

    uuid: str = Field(min_length=8)
    description: str | None = Field(default=None, max_length=4096)
    project: str | None = Field(default=None, max_length=256)
    priority: str | None = Field(default=None)
    due: str | None = Field(default=None, max_length=64)
    scheduled: str | None = Field(default=None, max_length=64)
    wait: str | None = Field(default=None, max_length=64)
    recur: str | None = Field(default=None, max_length=64)
    tags_add: list[str] | None = Field(default=None)
    tags_remove: list[str] | None = Field(default=None)

    @field_validator("uuid")
    @classmethod
    def valid_uuid(cls, v: str) -> str:
        return _check_uuid(v)

    @field_validator("description", "project", "due", "scheduled", "wait", "recur", mode="before")
    @classmethod
    def no_shell_injection(cls, v: str | None) -> str | None:
        if v is not None:
            _check_shell_injection(v)
        return v

    @field_validator("priority")
    @classmethod
    def valid_priority(cls, v: str | None) -> str | None:
        if v is not None and v not in _VALID_PRIORITIES:
            raise ValueError(f"Priority muss H, M oder L sein, nicht '{v}'")
        return v

    @field_validator("tags_add", "tags_remove", mode="before")
    @classmethod
    def valid_tags(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            for tag in v:
                if not _TAG_PATTERN.match(tag):
                    raise ValueError(
                        f"Tag '{tag}' enthält ungültige Zeichen. Nur Wörter, Bindestriche und Punkte erlaubt."
                    )
        return v


class TaskListInput(BaseModel):
    """Parameter für task_list."""

    filter_expr: str | None = Field(default=None, max_length=1024)
    project: str | None = Field(default=None, max_length=256)
    tags: list[str] | None = Field(default=None)
    status: str = Field(default="pending")
    limit: int = Field(default=50, ge=1, le=1000)

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        if v not in _VALID_STATUSES:
            raise ValueError(
                f"Ungültiger Status '{v}'. Erlaubt: {', '.join(sorted(_VALID_STATUSES))}"
            )
        return v

    @field_validator("filter_expr", "project", mode="before")
    @classmethod
    def no_shell_injection(cls, v: str | None) -> str | None:
        if v is not None:
            _check_shell_injection(v)
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def valid_tags(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            for tag in v:
                if not _TAG_PATTERN.match(tag):
                    raise ValueError(
                        f"Tag '{tag}' enthält ungültige Zeichen."
                    )
        return v


class UUIDInput(BaseModel):
    """Einfache UUID-Eingabe für task_get, task_done, task_delete, task_start, task_stop."""

    uuid: str = Field(min_length=8)

    @field_validator("uuid")
    @classmethod
    def valid_uuid(cls, v: str) -> str:
        return _check_uuid(v)
