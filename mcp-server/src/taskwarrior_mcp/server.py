"""FastMCP Server für Taskwarrior — registriert alle 11 Tools."""

import logging
import shlex
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from taskwarrior_mcp.config import Settings
from taskwarrior_mcp.models import TaskAddInput, TaskListInput, TaskModifyInput, UUIDInput
from taskwarrior_mcp.taskwarrior import TaskwarriorClient, TaskwarriorError

# Logging-Setup: KEIN print() — stdio ist für MCP-Protokoll reserviert
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """Hält den TaskwarriorClient für die Lebensdauer des Servers."""

    tw: TaskwarriorClient
    settings: Settings


@asynccontextmanager
async def lifespan(server: FastMCP):  # noqa: ANN001
    """Initialisiert den TaskwarriorClient beim Server-Start."""
    settings = Settings()
    logging.getLogger().setLevel(settings.log_level)
    try:
        tw = TaskwarriorClient(settings)
        logger.info("TaskwarriorClient initialisiert (TW %s)", tw.version)
        yield AppContext(tw=tw, settings=settings)
    except TaskwarriorError as exc:
        logger.error("Taskwarrior-Initialisierung fehlgeschlagen: %s", exc)
        raise


mcp = FastMCP("Taskwarrior", json_response=True, lifespan=lifespan)


def _get_tw(ctx: Context) -> TaskwarriorClient:
    """Hilfsfunktion: Holt den TaskwarriorClient aus dem Lifespan-Context."""
    return ctx.request_context.lifespan_context.tw


def _get_settings(ctx: Context) -> Settings:
    """Hilfsfunktion: Holt die Settings aus dem Lifespan-Context."""
    return ctx.request_context.lifespan_context.settings


# ---------------------------------------------------------------------------
# Lese-Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def task_list(
    ctx: Context,
    filter_expr: str | None = None,
    project: str | None = None,
    tags: list[str] | None = None,
    status: str = "pending",
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Liste Tasks mit optionalen Filtern auf.

    filter_expr unterstützt native Taskwarrior-Syntax:
      'project:Work +urgent due.before:eow'
      'status:pending priority:H'
      '+OVERDUE'
      'description.contains:meeting'
    """
    inp = TaskListInput(
        filter_expr=filter_expr,
        project=project,
        tags=tags,
        status=status,
        limit=limit,
    )
    tw = _get_tw(ctx)
    filter_args: list[str] = []
    if inp.filter_expr:
        filter_args.extend(shlex.split(inp.filter_expr))  # ← shlex, NICHT str.split
    if inp.project:
        filter_args.append(f"project:{inp.project}")
    if inp.tags:
        filter_args.extend(f"+{t}" for t in inp.tags)
    filter_args.append(f"status:{inp.status}")
    filter_args.append(f"limit:{inp.limit}")
    return tw.export_tasks(filter_args)


@mcp.tool()
async def task_get(
    ctx: Context,
    uuid: str,
) -> dict[str, Any]:
    """Gibt einen einzelnen Task per UUID zurück.

    Unterstützt vollständige UUIDs und Präfixe (mind. 8 Zeichen).
    """
    inp = UUIDInput(uuid=uuid)
    tw = _get_tw(ctx)
    return tw.get_task(inp.uuid)


@mcp.tool()
async def task_projects(ctx: Context) -> str:
    """Gibt eine Liste aller Projekte mit Task-Anzahl zurück."""
    tw = _get_tw(ctx)
    return tw.get_projects()


@mcp.tool()
async def task_tags(ctx: Context) -> str:
    """Gibt eine Liste aller Tags zurück."""
    tw = _get_tw(ctx)
    return tw.get_tags()


@mcp.tool()
async def task_stats(ctx: Context) -> str:
    """Gibt Taskwarrior-Statistiken zurück (Anzahl Tasks, Velocity etc.)."""
    tw = _get_tw(ctx)
    return tw.get_stats()


# ---------------------------------------------------------------------------
# Schreib-Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def task_add(
    ctx: Context,
    description: str,
    project: str | None = None,
    priority: str | None = None,
    due: str | None = None,
    tags: list[str] | None = None,
    scheduled: str | None = None,
    wait: str | None = None,
    recur: str | None = None,
) -> dict[str, Any]:
    """Fügt einen neuen Task hinzu und gibt ihn mit UUID zurück.

    priority: H (Hoch), M (Mittel), L (Niedrig)
    due/scheduled/wait: Taskwarrior-Datumsformat (today, tomorrow, eow, eom, +2d, 2025-03-15)
    recur: Wiederholungsintervall (daily, weekly, monthly, +2w, ...)
    """
    inp = TaskAddInput(
        description=description,
        project=project,
        priority=priority,
        due=due,
        tags=tags,
        scheduled=scheduled,
        wait=wait,
        recur=recur,
    )
    tw = _get_tw(ctx)
    attrs: dict[str, Any] = {}
    if inp.project:
        attrs["project"] = inp.project
    if inp.priority:
        attrs["priority"] = inp.priority
    if inp.due:
        attrs["due"] = inp.due
    if inp.scheduled:
        attrs["scheduled"] = inp.scheduled
    if inp.wait:
        attrs["wait"] = inp.wait
    if inp.recur:
        attrs["recur"] = inp.recur
    if inp.tags:
        attrs["tags"] = inp.tags
    return tw.add_task(inp.description, **attrs)


@mcp.tool()
async def task_modify(
    ctx: Context,
    uuid: str,
    description: str | None = None,
    project: str | None = None,
    priority: str | None = None,
    due: str | None = None,
    scheduled: str | None = None,
    wait: str | None = None,
    recur: str | None = None,
    tags_add: list[str] | None = None,
    tags_remove: list[str] | None = None,
) -> dict[str, Any]:
    """Ändert Attribute eines bestehenden Tasks.

    tags_add: Tags hinzufügen
    tags_remove: Tags entfernen
    priority entfernen: priority=None (setzt priority zurück)
    """
    inp = TaskModifyInput(
        uuid=uuid,
        description=description,
        project=project,
        priority=priority,
        due=due,
        scheduled=scheduled,
        wait=wait,
        recur=recur,
        tags_add=tags_add,
        tags_remove=tags_remove,
    )
    tw = _get_tw(ctx)
    attrs: dict[str, Any] = {}
    if inp.description is not None:
        attrs["description"] = inp.description
    if inp.project is not None:
        attrs["project"] = inp.project
    if inp.priority is not None:
        attrs["priority"] = inp.priority
    if inp.due is not None:
        attrs["due"] = inp.due
    if inp.scheduled is not None:
        attrs["scheduled"] = inp.scheduled
    if inp.wait is not None:
        attrs["wait"] = inp.wait
    if inp.recur is not None:
        attrs["recur"] = inp.recur
    if inp.tags_add is not None:
        attrs["tags_add"] = inp.tags_add
    if inp.tags_remove is not None:
        attrs["tags_remove"] = inp.tags_remove
    return tw.modify_task(inp.uuid, **attrs)


@mcp.tool()
async def task_done(
    ctx: Context,
    uuid: str,
) -> str:
    """Markiert einen Task als erledigt (done).

    Gibt eine Bestätigungsmeldung zurück.
    """
    inp = UUIDInput(uuid=uuid)
    tw = _get_tw(ctx)
    return tw.complete_task(inp.uuid)


@mcp.tool()
async def task_delete(
    ctx: Context,
    uuid: str,
) -> str:
    """Löscht einen Task dauerhaft.

    ACHTUNG: Diese Operation kann nicht rückgängig gemacht werden.
    Vor dem Aufruf beim Benutzer bestätigen lassen.
    """
    inp = UUIDInput(uuid=uuid)
    tw = _get_tw(ctx)
    return tw.delete_task(inp.uuid)


@mcp.tool()
async def task_start(
    ctx: Context,
    uuid: str,
) -> dict[str, Any]:
    """Startet die Zeiterfassung für einen Task (setzt ihn auf 'active').

    Gibt den aktualisierten Task zurück.
    """
    inp = UUIDInput(uuid=uuid)
    tw = _get_tw(ctx)
    return tw.start_task(inp.uuid)


@mcp.tool()
async def task_stop(
    ctx: Context,
    uuid: str,
) -> dict[str, Any]:
    """Stoppt die Zeiterfassung für einen aktiven Task.

    Gibt den aktualisierten Task zurück.
    """
    inp = UUIDInput(uuid=uuid)
    tw = _get_tw(ctx)
    return tw.stop_task(inp.uuid)
