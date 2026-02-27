"""Unit-Tests für TaskwarriorClient.

Alle Tests mocken subprocess.run und verifizieren:
- shell=False wird IMMER verwendet
- Korrekte Argument-Listen werden aufgebaut
- Exit-Code 1 ist kein Fehler
- Exit-Code ≥2 wirft TaskwarriorError
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from taskwarrior_mcp.config import Settings
from taskwarrior_mcp.taskwarrior import TaskwarriorClient, TaskwarriorError


@pytest.fixture()
def settings() -> Settings:
    return Settings(task_binary="task", command_timeout=10)


@pytest.fixture()
def mock_subprocess():
    """Mockt subprocess.run für alle Tests."""
    with patch("taskwarrior_mcp.taskwarrior.subprocess.run") as mock_run:
        # Standard-Antwort für _verify_installation
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="3.0.0\n",
            stderr="",
        )
        yield mock_run


@pytest.fixture()
def client(settings: Settings, mock_subprocess: MagicMock) -> TaskwarriorClient:
    """Erstellt einen TaskwarriorClient mit gemocktem subprocess."""
    return TaskwarriorClient(settings)


class TestShellFalse:
    """Verifiziert dass shell=False IMMER verwendet wird."""

    def test_verify_installation_uses_shell_false(self, settings: Settings):
        with patch("taskwarrior_mcp.taskwarrior.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="3.0.0\n", stderr="")
            TaskwarriorClient(settings)
            for call_args in mock_run.call_args_list:
                assert call_args.kwargs.get("shell") is False, (
                    "subprocess.run muss shell=False verwenden!"
                )

    def test_run_uses_shell_false(self, client: TaskwarriorClient, mock_subprocess: MagicMock):
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="[]", stderr="")
        client._run(["export"])
        # Letzter Aufruf (export, nicht --version)
        last_call = mock_subprocess.call_args
        assert last_call.kwargs.get("shell") is False

    def test_export_tasks_uses_shell_false(self, client: TaskwarriorClient, mock_subprocess: MagicMock):
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="[]", stderr="")
        client.export_tasks([])
        last_call = mock_subprocess.call_args
        assert last_call.kwargs.get("shell") is False


class TestExitCodes:
    """Verifiziert korrektes Verhalten bei verschiedenen Exit-Codes."""

    def test_exit_code_0_is_success(self, client: TaskwarriorClient, mock_subprocess: MagicMock):
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="[]", stderr="")
        result = client.export_tasks()
        assert result == []

    def test_exit_code_1_is_not_an_error(self, client: TaskwarriorClient, mock_subprocess: MagicMock):
        """Exit-Code 1 = 'no matching tasks' — kein Fehler!"""
        mock_subprocess.return_value = MagicMock(returncode=1, stdout="", stderr="")
        # Darf KEINE Exception werfen
        result = client.export_tasks()
        assert result == []

    def test_exit_code_2_raises_error(self, client: TaskwarriorClient, mock_subprocess: MagicMock):
        mock_subprocess.return_value = MagicMock(
            returncode=2, stdout="", stderr="Taskwarrior config error"
        )
        with pytest.raises(TaskwarriorError, match="config error"):
            client.export_tasks()

    def test_exit_code_higher_raises_error(self, client: TaskwarriorClient, mock_subprocess: MagicMock):
        mock_subprocess.return_value = MagicMock(
            returncode=5, stdout="", stderr="Fatal error"
        )
        with pytest.raises(TaskwarriorError):
            client._run(["some", "command"])


class TestExportTasks:
    """Tests für export_tasks."""

    def test_returns_empty_list_on_empty_output(
        self, client: TaskwarriorClient, mock_subprocess: MagicMock
    ):
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
        assert client.export_tasks() == []

    def test_parses_json_output(self, client: TaskwarriorClient, mock_subprocess: MagicMock):
        tasks = [{"uuid": "abc123", "description": "Test-Task", "status": "pending"}]
        mock_subprocess.return_value = MagicMock(
            returncode=0, stdout=json.dumps(tasks), stderr=""
        )
        result = client.export_tasks()
        assert result == tasks

    def test_appends_export_to_args(self, client: TaskwarriorClient, mock_subprocess: MagicMock):
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="[]", stderr="")
        client.export_tasks(["status:pending"])
        last_call = mock_subprocess.call_args
        cmd = last_call.args[0]
        assert "export" in cmd
        assert "status:pending" in cmd


class TestAddTask:
    """Tests für add_task."""

    def test_add_task_returns_task_with_uuid(
        self, client: TaskwarriorClient, mock_subprocess: MagicMock
    ):
        new_task = {
            "uuid": "12345678-1234-1234-1234-123456789012",
            "description": "Neuer Task",
            "status": "pending",
        }
        # add gibt nichts zurück, dann +LATEST export gibt Task zurück
        mock_subprocess.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),       # add
            MagicMock(returncode=0, stdout=json.dumps([new_task]), stderr=""),  # +LATEST export
        ]
        result = client.add_task("Neuer Task")
        assert result["uuid"] == "12345678-1234-1234-1234-123456789012"

    def test_add_task_includes_project(self, client: TaskwarriorClient, mock_subprocess: MagicMock):
        mock_subprocess.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=0, stdout="[]", stderr=""),
        ]
        client.add_task("Task", project="Arbeit")
        # call_args_list[0] = _verify_installation, [1] = add, [2] = +LATEST export
        first_run = mock_subprocess.call_args_list[1]
        cmd = first_run.args[0]
        assert "project:Arbeit" in cmd

    def test_add_task_includes_tags(self, client: TaskwarriorClient, mock_subprocess: MagicMock):
        mock_subprocess.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=0, stdout="[]", stderr=""),
        ]
        client.add_task("Task", tags=["urgent", "work"])
        first_run = mock_subprocess.call_args_list[1]
        cmd = first_run.args[0]
        assert "+urgent" in cmd
        assert "+work" in cmd


class TestGetTask:
    """Tests für get_task."""

    def test_get_task_raises_if_not_found(
        self, client: TaskwarriorClient, mock_subprocess: MagicMock
    ):
        mock_subprocess.return_value = MagicMock(returncode=1, stdout="", stderr="")
        with pytest.raises(TaskwarriorError, match="nicht gefunden"):
            client.get_task("nonexistent-uuid")

    def test_get_task_returns_task(self, client: TaskwarriorClient, mock_subprocess: MagicMock):
        task = {"uuid": "abc123", "description": "Test"}
        mock_subprocess.return_value = MagicMock(
            returncode=0, stdout=json.dumps([task]), stderr=""
        )
        result = client.get_task("abc123")
        assert result == task


class TestBuildCommand:
    """Tests für _build_command."""

    def test_includes_standard_overrides(self, client: TaskwarriorClient):
        cmd = client._build_command(["export"])
        assert "rc.verbose=nothing" in cmd
        assert "rc.confirmation=no" in cmd
        assert "rc.bulk=0" in cmd
        assert "rc.json.array=on" in cmd

    def test_includes_taskrc_if_set(self, settings: Settings, mock_subprocess: MagicMock):
        settings.taskrc = "/path/to/.taskrc"
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="3.0.0\n", stderr="")
        client = TaskwarriorClient(settings)
        cmd = client._build_command(["export"])
        assert "rc:/path/to/.taskrc" in cmd

    def test_includes_data_location_if_set(self, settings: Settings, mock_subprocess: MagicMock):
        settings.task_data = "/path/to/data"
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="3.0.0\n", stderr="")
        client = TaskwarriorClient(settings)
        cmd = client._build_command(["export"])
        assert "rc.data.location=/path/to/data" in cmd


class TestTimeout:
    """Tests für Timeout-Handling."""

    def test_timeout_raises_taskwarrior_error(
        self, client: TaskwarriorClient, mock_subprocess: MagicMock
    ):
        import subprocess as sp
        mock_subprocess.side_effect = sp.TimeoutExpired(cmd="task", timeout=10)
        with pytest.raises(TaskwarriorError, match="Timeout"):
            client._run(["export"])


class TestInstallationCheck:
    """Tests für _verify_installation."""

    def test_missing_binary_raises_error(self, settings: Settings):
        with patch("taskwarrior_mcp.taskwarrior.shutil.which", return_value=None):
            with pytest.raises(TaskwarriorError, match="not found in PATH"):
                TaskwarriorClient(settings)

    def test_version_parsed_correctly(self, settings: Settings):
        with patch("taskwarrior_mcp.taskwarrior.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="3.1.2\n", stderr="")
            client = TaskwarriorClient(settings)
            assert client.version == "3.1.2"
            assert client.major_version == 3
