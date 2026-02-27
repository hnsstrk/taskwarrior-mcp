"""Integration-Tests für Taskwarrior MCP Server Tools.

Nutzt echte Taskwarrior-Installation in isolierter Umgebung (tmp_path).
Tests werden übersprungen wenn Taskwarrior nicht installiert ist.
"""

import pytest

from tests.conftest import requires_taskwarrior
from taskwarrior_mcp.taskwarrior import TaskwarriorClient, TaskwarriorError


@requires_taskwarrior
class TestCRUDCycle:
    """Vollständiger CRUD-Zyklus mit echtem Taskwarrior."""

    def test_add_task_returns_uuid(self, isolated_client: TaskwarriorClient):
        task = isolated_client.add_task("Integration-Test Task")
        assert "uuid" in task
        assert len(task["uuid"]) == 36  # Standard UUID-Format
        assert task["description"] == "Integration-Test Task"
        assert task["status"] == "pending"

    def test_add_task_with_project(self, isolated_client: TaskwarriorClient):
        task = isolated_client.add_task("Task mit Projekt", project="TestProjekt")
        assert task["project"] == "TestProjekt"

    def test_add_task_with_priority(self, isolated_client: TaskwarriorClient):
        task = isolated_client.add_task("Wichtiger Task", priority="H")
        assert task["priority"] == "H"

    def test_add_task_with_tags(self, isolated_client: TaskwarriorClient):
        task = isolated_client.add_task("Tag-Task", tags=["urgent", "work"])
        tags = task.get("tags", [])
        assert "urgent" in tags
        assert "work" in tags

    def test_get_task_by_uuid(self, isolated_client: TaskwarriorClient):
        added = isolated_client.add_task("Task zum Abrufen")
        uuid = added["uuid"]
        retrieved = isolated_client.get_task(uuid)
        assert retrieved["uuid"] == uuid
        assert retrieved["description"] == "Task zum Abrufen"

    def test_get_task_by_prefix(self, isolated_client: TaskwarriorClient):
        added = isolated_client.add_task("Task mit UUID-Prefix")
        uuid = added["uuid"]
        prefix = uuid[:8]
        retrieved = isolated_client.get_task(prefix)
        assert retrieved["uuid"] == uuid

    def test_get_nonexistent_task_raises(self, isolated_client: TaskwarriorClient):
        with pytest.raises(TaskwarriorError):
            isolated_client.get_task("00000000-0000-0000-0000-000000000000")

    def test_modify_task_description(self, isolated_client: TaskwarriorClient):
        added = isolated_client.add_task("Original Beschreibung")
        uuid = added["uuid"]
        modified = isolated_client.modify_task(uuid, description="Neue Beschreibung")
        assert modified["description"] == "Neue Beschreibung"

    def test_modify_task_project(self, isolated_client: TaskwarriorClient):
        added = isolated_client.add_task("Task ohne Projekt")
        uuid = added["uuid"]
        modified = isolated_client.modify_task(uuid, project="NeuesProjekt")
        assert modified["project"] == "NeuesProjekt"

    def test_complete_task(self, isolated_client: TaskwarriorClient):
        added = isolated_client.add_task("Task abschließen")
        uuid = added["uuid"]
        isolated_client.complete_task(uuid)
        # Abgeschlossener Task sollte in pending nicht mehr auftauchen
        pending = isolated_client.export_tasks(["status:pending"])
        uuids = [t["uuid"] for t in pending]
        assert uuid not in uuids

    def test_delete_task(self, isolated_client: TaskwarriorClient):
        added = isolated_client.add_task("Task löschen")
        uuid = added["uuid"]
        isolated_client.delete_task(uuid)
        # Gelöschter Task nicht mehr in pending
        pending = isolated_client.export_tasks(["status:pending"])
        uuids = [t["uuid"] for t in pending]
        assert uuid not in uuids

    def test_start_and_stop_task(self, isolated_client: TaskwarriorClient):
        added = isolated_client.add_task("Zeiterfassung-Task")
        uuid = added["uuid"]

        started = isolated_client.start_task(uuid)
        assert started.get("start") is not None

        stopped = isolated_client.stop_task(uuid)
        # Nach stop: kein aktiver Start mehr
        assert stopped.get("start") is None


@requires_taskwarrior
class TestExportFilters:
    """Tests für export_tasks mit verschiedenen Filtern."""

    def test_export_empty_returns_list(self, isolated_client: TaskwarriorClient):
        result = isolated_client.export_tasks(["status:pending"])
        assert isinstance(result, list)

    def test_export_with_project_filter(self, isolated_client: TaskwarriorClient):
        isolated_client.add_task("Arbeit-Task", project="Arbeit")
        isolated_client.add_task("Privat-Task", project="Privat")

        arbeit_tasks = isolated_client.export_tasks(["project:Arbeit", "status:pending"])
        assert all(t.get("project") == "Arbeit" for t in arbeit_tasks)
        assert len(arbeit_tasks) >= 1

    def test_export_nonexistent_project_returns_empty(self, isolated_client: TaskwarriorClient):
        result = isolated_client.export_tasks(["project:GibtEsNicht", "status:pending"])
        assert result == []


@requires_taskwarrior
class TestProjectsAndTags:
    """Tests für Metadaten-Abfragen."""

    def test_get_projects_returns_string(self, isolated_client: TaskwarriorClient):
        isolated_client.add_task("Test", project="TestProjekt")
        result = isolated_client.get_projects()
        assert isinstance(result, str)

    def test_get_tags_returns_string(self, isolated_client: TaskwarriorClient):
        isolated_client.add_task("Test", tags=["test-tag"])
        result = isolated_client.get_tags()
        assert isinstance(result, str)

    def test_get_stats_returns_string(self, isolated_client: TaskwarriorClient):
        result = isolated_client.get_stats()
        assert isinstance(result, str)


@requires_taskwarrior
class TestVersionDetection:
    """Tests für Versions-Erkennung."""

    def test_client_detects_version(self, isolated_client: TaskwarriorClient):
        assert isolated_client.version != ""
        assert isolated_client.major_version in (2, 3)
