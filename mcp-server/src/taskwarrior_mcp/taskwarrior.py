"""CLI-Wrapper für Taskwarrior — kapselt alle subprocess-Aufrufe."""

import json
import logging
import shutil
import subprocess

from taskwarrior_mcp.config import Settings

logger = logging.getLogger(__name__)


class TaskwarriorError(Exception):
    """Fehler bei der Taskwarrior-Ausführung."""


class TaskwarriorClient:
    """Wrapper um die Taskwarrior CLI.

    Alle subprocess-Aufrufe nutzen shell=False mit Liste als Argumente.
    Exit-Code 1 bedeutet "keine Ergebnisse" und ist kein Fehler.
    Nur Exit-Code ≥2 ist ein tatsächlicher Fehler.
    """

    STANDARD_OVERRIDES = [
        "rc.verbose=nothing",
        "rc.confirmation=no",
        "rc.bulk=0",
        "rc.json.array=on",
    ]

    def __init__(self, settings: Settings) -> None:
        self.task_bin = settings.task_binary
        self.data_location = settings.task_data
        self.taskrc = settings.taskrc
        self.timeout = settings.command_timeout
        self.auto_sync = settings.auto_sync
        self._verify_installation()

    def _verify_installation(self) -> None:
        """Prüft ob Taskwarrior installiert ist und ermittelt die Version."""
        if not shutil.which(self.task_bin):
            raise TaskwarriorError(f"'{self.task_bin}' not found in PATH")
        # Für --version keine STANDARD_OVERRIDES nutzen
        result = subprocess.run(
            [self.task_bin, "--version"],
            capture_output=True,
            text=True,
            timeout=self.timeout,
            shell=False,
            check=False,
        )
        self.version = result.stdout.strip()
        try:
            self.major_version = int(self.version.split(".")[0])
        except (ValueError, IndexError):
            self.major_version = 2
        logger.info("Taskwarrior %s gefunden", self.version)

    def _build_command(self, args: list[str]) -> list[str]:
        """Baut den vollständigen Befehl mit Overrides auf."""
        cmd = [self.task_bin]
        if self.taskrc:
            cmd.append(f"rc:{self.taskrc}")
        if self.data_location:
            cmd.append(f"rc.data.location={self.data_location}")
        cmd.extend(self.STANDARD_OVERRIDES)
        cmd.extend(args)
        return cmd

    def _run(self, args: list[str]) -> str:
        """Führt einen Taskwarrior-Befehl aus und gibt stdout zurück.

        WICHTIG: shell=False ist Pflicht. Niemals shell=True verwenden.
        Exit-Code 1 = "no matching tasks" — kein Fehler.
        Nur Exit-Code ≥2 ist ein tatsächlicher Fehler.
        """
        cmd = self._build_command(args)
        logger.debug("Ausführen: %s", cmd)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                shell=False,        # ← NIEMALS True
                check=False,
            )
            # Exit-Code 1 = "no matching tasks" — kein Fehler
            if result.returncode == 1 and result.stderr.strip():
                logger.debug("Exit-Code 1 mit stderr: %s", result.stderr.strip())
            if result.returncode >= 2:
                error_msg = result.stderr.strip() or result.stdout.strip()
                if error_msg:
                    raise TaskwarriorError(error_msg)
            return result.stdout
        except subprocess.TimeoutExpired as exc:
            raise TaskwarriorError(f"Timeout nach {self.timeout}s") from exc
        except FileNotFoundError as exc:
            raise TaskwarriorError(f"Binary '{self.task_bin}' nicht gefunden") from exc

    def export_tasks(self, filter_args: list[str] | None = None) -> list[dict]:
        """Exportiert Tasks als JSON-Liste.

        Args:
            filter_args: Taskwarrior-Filterargumente als Liste (bereits aufgesplittet).
                         Für Filter-Strings: shlex.split() verwenden, NICHT str.split()!
        """
        args = (filter_args or []) + ["export"]
        raw = self._run(args)
        if not raw.strip():
            return []
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning("JSON-Parsing fehlgeschlagen: %s", exc)
            return []

    def add_task(self, description: str, **attrs) -> dict:
        """Fügt einen neuen Task hinzu und gibt ihn mit UUID zurück.

        Nach dem Hinzufügen wird +LATEST export aufgerufen um die UUID zu erhalten.
        """
        args = ["add", description]
        for key, value in attrs.items():
            if value is None:
                continue
            if key == "tags":
                args.extend(f"+{tag}" for tag in value)
            else:
                args.append(f"{key}:{value}")
        self._run(args)
        # UUID des neu erstellten Tasks via +LATEST abrufen
        tasks = self.export_tasks(["+LATEST", "limit:1"])
        if tasks:
            return tasks[0]
        return {"error": "Task erstellt, aber Abruf fehlgeschlagen"}

    def get_task(self, uuid: str) -> dict:
        """Gibt einen einzelnen Task per UUID zurück."""
        tasks = self.export_tasks([uuid])
        if not tasks:
            raise TaskwarriorError(f"Task {uuid} nicht gefunden")
        return tasks[0]

    def modify_task(self, uuid: str, **attrs) -> dict:
        """Ändert Attribute eines Tasks und gibt den aktualisierten Task zurück."""
        args = [uuid, "modify"]
        for key, value in attrs.items():
            if value is None:
                continue
            if key == "tags_add":
                args.extend(f"+{tag}" for tag in value)
            elif key == "tags_remove":
                args.extend(f"-{tag}" for tag in value)
            else:
                args.append(f"{key}:{value}")
        self._run(args)
        return self.get_task(uuid)

    def complete_task(self, uuid: str) -> str:
        """Markiert einen Task als erledigt."""
        result = self._run([uuid, "done"]).strip()
        if self.auto_sync:
            self._sync_silent()
        return result

    def delete_task(self, uuid: str) -> str:
        """Löscht einen Task."""
        result = self._run([uuid, "delete"]).strip()
        if self.auto_sync:
            self._sync_silent()
        return result

    def start_task(self, uuid: str) -> dict:
        """Startet die Zeiterfassung für einen Task."""
        self._run([uuid, "start"])
        return self.get_task(uuid)

    def stop_task(self, uuid: str) -> dict:
        """Stoppt die Zeiterfassung für einen Task."""
        self._run([uuid, "stop"])
        return self.get_task(uuid)

    def _sync_silent(self) -> None:
        """Führt task sync durch, ignoriert Fehler (z.B. kein Server konfiguriert)."""
        try:
            self._run(["sync"])
        except TaskwarriorError as exc:
            logger.debug("Auto-Sync fehlgeschlagen (ignoriert): %s", exc)

    def sync(self) -> str:
        """Synchronisiert mit dem Taskserver."""
        return self._run(["sync"]).strip()

    def get_projects(self) -> str:
        """Gibt eine Liste aller Projekte zurück."""
        return self._run(["projects"]).strip()

    def get_tags(self) -> str:
        """Gibt eine Liste aller Tags zurück."""
        return self._run(["tags"]).strip()

    def get_stats(self) -> str:
        """Gibt Statistiken zurück."""
        return self._run(["stats"]).strip()
