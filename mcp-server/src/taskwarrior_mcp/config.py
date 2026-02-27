"""Konfiguration für den Taskwarrior MCP Server via Pydantic BaseSettings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Server-Konfiguration. Alle Werte können über Umgebungsvariablen mit Präfix TW_MCP_ gesetzt werden.

    Beispiele:
        TW_MCP_TASK_BINARY=task
        TW_MCP_DEFAULT_LIMIT=100
        TW_MCP_LOG_LEVEL=DEBUG
    """

    task_binary: str = "task"
    task_data: str | None = None        # Override rc.data.location
    taskrc: str | None = None           # Override TASKRC path
    default_limit: int = 50
    command_timeout: int = 30
    log_level: str = "INFO"
    auto_sync: bool = False             # task sync nach Schreiboperationen

    model_config = {"env_prefix": "TW_MCP_"}
