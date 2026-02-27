"""Unit-Tests für Pydantic Input-Validation (models.py).

Verifiziert:
- Shell-Injection-Prevention
- Priority-Validierung
- Tag-Validierung
- UUID-Validierung
"""

import pytest
from pydantic import ValidationError

from taskwarrior_mcp.models import TaskAddInput, TaskListInput, TaskModifyInput, UUIDInput


class TestShellInjectionPrevention:
    """Testet die Shell-Injection-Abwehr."""

    INJECTION_STRINGS = [
        "Task; rm -rf /",
        "Task | cat /etc/passwd",
        "Task & background_cmd",
        "Task `whoami`",
        "Task $(id)",
        "Task ${HOME}",
        "Task { echo evil }",
        "Task \\ escaped",
    ]

    @pytest.mark.parametrize("evil_input", INJECTION_STRINGS)
    def test_blocks_shell_injection_in_description(self, evil_input: str):
        with pytest.raises(ValidationError):
            TaskAddInput(description=evil_input)

    @pytest.mark.parametrize("evil_input", INJECTION_STRINGS)
    def test_blocks_shell_injection_in_project(self, evil_input: str):
        with pytest.raises(ValidationError):
            TaskAddInput(description="Normaler Task", project=evil_input)

    @pytest.mark.parametrize("evil_input", INJECTION_STRINGS)
    def test_blocks_shell_injection_in_filter_expr(self, evil_input: str):
        with pytest.raises(ValidationError):
            TaskListInput(filter_expr=evil_input)

    def test_allows_normal_description(self):
        inp = TaskAddInput(description="Normaler Task ohne Sonderzeichen")
        assert inp.description == "Normaler Task ohne Sonderzeichen"

    def test_allows_punctuation_in_description(self):
        """Punkte, Kommas, Klammern etc. sind erlaubt."""
        inp = TaskAddInput(description="Einkaufen: Milch, Brot (2x), Äpfel")
        assert inp.description == "Einkaufen: Milch, Brot (2x), Äpfel"

    def test_allows_hyphen_in_description(self):
        inp = TaskAddInput(description="E-Mail schreiben an Max-Müller")
        assert inp.description == "E-Mail schreiben an Max-Müller"

    @pytest.mark.parametrize("field", ["due", "scheduled", "wait", "recur"])
    @pytest.mark.parametrize("evil_input", [
        "tomorrow; rm -rf /",
        "eow | cat /etc/passwd",
        "today & evil",
        "$(date)",
        "`date`",
    ])
    def test_blocks_shell_injection_in_date_fields_add(self, field: str, evil_input: str):
        with pytest.raises(ValidationError):
            TaskAddInput(description="Test", **{field: evil_input})

    @pytest.mark.parametrize("field", ["due", "scheduled", "wait", "recur"])
    @pytest.mark.parametrize("evil_input", [
        "tomorrow; rm -rf /",
        "eow | cat /etc/passwd",
        "$(date)",
    ])
    def test_blocks_shell_injection_in_date_fields_modify(self, field: str, evil_input: str):
        with pytest.raises(ValidationError):
            TaskModifyInput(uuid="abcdef12", **{field: evil_input})

    @pytest.mark.parametrize("field", ["due", "scheduled", "wait", "recur"])
    @pytest.mark.parametrize("valid_input", [
        "today", "tomorrow", "eow", "eom", "+2d", "2025-12-31", "monday", "weekly",
    ])
    def test_allows_valid_date_fields(self, field: str, valid_input: str):
        inp = TaskAddInput(description="Test", **{field: valid_input})
        assert getattr(inp, field) == valid_input


class TestPriorityValidation:
    """Testet die Priority-Validierung."""

    def test_valid_priorities(self):
        for priority in ["H", "M", "L"]:
            inp = TaskAddInput(description="Test", priority=priority)
            assert inp.priority == priority

    def test_invalid_priority_raises(self):
        with pytest.raises(ValidationError):
            TaskAddInput(description="Test", priority="X")

    def test_lowercase_priority_raises(self):
        with pytest.raises(ValidationError):
            TaskAddInput(description="Test", priority="h")

    def test_none_priority_allowed(self):
        inp = TaskAddInput(description="Test", priority=None)
        assert inp.priority is None


class TestTagValidation:
    """Testet die Tag-Validierung."""

    def test_valid_simple_tag(self):
        inp = TaskAddInput(description="Test", tags=["urgent"])
        assert inp.tags == ["urgent"]

    def test_valid_hyphenated_tag(self):
        inp = TaskAddInput(description="Test", tags=["high-priority"])
        assert inp.tags == ["high-priority"]

    def test_valid_dotted_tag(self):
        inp = TaskAddInput(description="Test", tags=["v1.0.0"])
        assert inp.tags == ["v1.0.0"]

    def test_valid_multiple_tags(self):
        inp = TaskAddInput(description="Test", tags=["urgent", "work", "email"])
        assert inp.tags == ["urgent", "work", "email"]

    def test_invalid_tag_with_space(self):
        with pytest.raises(ValidationError):
            TaskAddInput(description="Test", tags=["invalid tag"])

    def test_invalid_tag_with_slash(self):
        with pytest.raises(ValidationError):
            TaskAddInput(description="Test", tags=["invalid/tag"])

    def test_invalid_tag_with_semicolon(self):
        with pytest.raises(ValidationError):
            TaskAddInput(description="Test", tags=["invalid;tag"])


class TestUUIDValidation:
    """Testet die UUID-Validierung."""

    def test_full_uuid_valid(self):
        inp = UUIDInput(uuid="12345678-1234-1234-1234-123456789012")
        assert inp.uuid == "12345678-1234-1234-1234-123456789012"

    def test_uuid_prefix_8_chars_valid(self):
        inp = UUIDInput(uuid="12345678")
        assert inp.uuid == "12345678"

    def test_uuid_too_short_raises(self):
        with pytest.raises(ValidationError):
            UUIDInput(uuid="1234567")  # 7 Zeichen — zu kurz

    def test_empty_uuid_raises(self):
        with pytest.raises(ValidationError):
            UUIDInput(uuid="")

    def test_uuid_with_shell_injection_raises(self):
        with pytest.raises(ValidationError):
            UUIDInput(uuid="abcdefgh; rm -rf /")

    def test_uuid_with_non_hex_chars_raises(self):
        with pytest.raises(ValidationError):
            UUIDInput(uuid="zzzzzzzz")

    def test_uuid_with_spaces_raises(self):
        with pytest.raises(ValidationError):
            UUIDInput(uuid="12345678 DROP TABLE")

    def test_modify_uuid_validated(self):
        with pytest.raises(ValidationError):
            TaskModifyInput(uuid="abcdefgh; rm -rf /")

    def test_modify_valid_uuid(self):
        inp = TaskModifyInput(uuid="abcdef12-3456-7890-abcd-ef1234567890")
        assert inp.uuid == "abcdef12-3456-7890-abcd-ef1234567890"


class TestTaskAddInput:
    """Tests für das TaskAddInput Model."""

    def test_minimal_valid_input(self):
        inp = TaskAddInput(description="Minimaler Task")
        assert inp.description == "Minimaler Task"
        assert inp.project is None
        assert inp.priority is None
        assert inp.due is None
        assert inp.tags is None

    def test_full_valid_input(self):
        inp = TaskAddInput(
            description="Vollständiger Task",
            project="Arbeit",
            priority="H",
            due="2025-12-31",
            tags=["urgent", "work"],
            scheduled="tomorrow",
            wait="monday",
            recur="weekly",
        )
        assert inp.description == "Vollständiger Task"
        assert inp.project == "Arbeit"
        assert inp.priority == "H"
        assert inp.due == "2025-12-31"
        assert inp.tags == ["urgent", "work"]

    def test_empty_description_raises(self):
        with pytest.raises(ValidationError):
            TaskAddInput(description="")


class TestTaskModifyInput:
    """Tests für das TaskModifyInput Model."""

    def test_minimal_valid_input(self):
        inp = TaskModifyInput(uuid="12345678")
        assert inp.uuid == "12345678"
        assert inp.description is None

    def test_tags_add_and_remove(self):
        inp = TaskModifyInput(
            uuid="12345678",
            tags_add=["new-tag"],
            tags_remove=["old-tag"],
        )
        assert inp.tags_add == ["new-tag"]
        assert inp.tags_remove == ["old-tag"]


class TestTaskListInput:
    """Tests für das TaskListInput Model."""

    def test_defaults(self):
        inp = TaskListInput()
        assert inp.status == "pending"
        assert inp.limit == 50
        assert inp.filter_expr is None

    def test_custom_limit(self):
        inp = TaskListInput(limit=100)
        assert inp.limit == 100

    def test_limit_too_large_raises(self):
        with pytest.raises(ValidationError):
            TaskListInput(limit=1001)

    def test_limit_zero_raises(self):
        with pytest.raises(ValidationError):
            TaskListInput(limit=0)

    def test_valid_filter_expr(self):
        inp = TaskListInput(filter_expr="project:Work due.before:eow")
        assert inp.filter_expr == "project:Work due.before:eow"

    @pytest.mark.parametrize("status", ["pending", "completed", "deleted", "waiting", "recurring"])
    def test_valid_status_values(self, status: str):
        inp = TaskListInput(status=status)
        assert inp.status == status

    @pytest.mark.parametrize("status", ["invalid", "active", "PENDING", "all", ""])
    def test_invalid_status_raises(self, status: str):
        with pytest.raises(ValidationError):
            TaskListInput(status=status)
