"""Test-Fixtures für Taskwarrior MCP Tests.

Stellt eine isolierte Taskwarrior-Umgebung via tmp_path bereit,
sodass echte Tests keine System-Taskwarrior-Daten beeinflussen.
"""

import subprocess
from pathlib import Path

import pytest

from taskwarrior_mcp.config import Settings
from taskwarrior_mcp.taskwarrior import TaskwarriorClient


@pytest.fixture()
def mock_settings() -> Settings:
    """Erstellt Settings für Unit-Tests (kein echtes Taskwarrior benötigt)."""
    return Settings(
        task_binary="task",
        default_limit=50,
        command_timeout=10,
        log_level="DEBUG",
    )


@pytest.fixture()
def tw_env(tmp_path: Path) -> dict[str, str]:
    """Erstellt eine isolierte Taskwarrior-Umgebung in tmp_path.

    Setzt TASKDATA und TASKRC auf temporäre Verzeichnisse,
    sodass Tests keine echten Taskwarrior-Daten lesen oder schreiben.
    """
    data_dir = tmp_path / "taskdata"
    data_dir.mkdir()
    taskrc = tmp_path / ".taskrc"
    taskrc.write_text(
        f"data.location={data_dir}\n"
        "confirmation=no\n"
        "verbose=nothing\n"
        "json.array=on\n"
        "bulk=0\n",
        encoding="utf-8",
    )
    return {
        "TASKDATA": str(data_dir),
        "TASKRC": str(taskrc),
        "data_dir": str(data_dir),
        "taskrc": str(taskrc),
    }


@pytest.fixture()
def isolated_settings(tw_env: dict[str, str]) -> Settings:
    """Settings für Integration-Tests mit isolierter TW-Umgebung."""
    return Settings(
        task_binary="task",
        task_data=tw_env["data_dir"],
        taskrc=tw_env["taskrc"],
        default_limit=50,
        command_timeout=10,
        log_level="DEBUG",
    )


@pytest.fixture()
def isolated_client(isolated_settings: Settings) -> TaskwarriorClient:
    """Echter TaskwarriorClient in isolierter Umgebung."""
    return TaskwarriorClient(isolated_settings)


def _is_taskwarrior_available() -> bool:
    """Prüft ob Taskwarrior auf dem System installiert ist."""
    try:
        result = subprocess.run(
            ["task", "--version"],
            capture_output=True,
            timeout=5,
            shell=False,
            check=False,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# Marker für Tests, die echtes Taskwarrior benötigen
requires_taskwarrior = pytest.mark.skipif(
    not _is_taskwarrior_available(),
    reason="Taskwarrior nicht installiert",
)
