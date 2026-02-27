---
description: "Taskwarrior sync and status overview"
disable-model-invocation: true
---

# Task Sync und Status

Synchronisiere Taskwarrior mit dem konfigurierten Server und zeige den aktuellen Status.

## Argumente

$ARGUMENTS (optional: "status" für nur Status ohne Sync, "full" für vollständigen Bericht)

## Ablauf

### 1. Aktueller Status (vor Sync)
- `task_stats` aufrufen
- Zeige: Gesamt offen, überfällig, heute fällig, aktive Tasks

### 2. Synchronisation
Sofern `$ARGUMENTS` nicht "status" ist:
- Führe Sync durch (wird vom MCP Server via `TW_MCP_AUTO_SYNC` gesteuert)
- Hinweis: Sync muss in Taskwarrior konfiguriert sein (taskd oder Inthe.AM)
- Bei Fehler: Zeige die Fehlermeldung und mögliche Ursachen

### 3. Status nach Sync
- `task_stats` erneut aufrufen
- Vergleiche mit Vorher-Status
- Zeige Änderungen (neue Tasks, abgeschlossene Tasks)

### 4. Schnellübersicht
Kompakter Überblick des aktuellen Zustands:
- `task_list` mit `filter_expr="+TODAY"` — Heute
- `task_list` mit `filter_expr="+OVERDUE"` — Überfällig
- `task_list` mit `filter_expr="+ACTIVE"` — Aktiv in Arbeit

### 5. Vollständiger Bericht (nur bei "full")
Wenn `$ARGUMENTS` "full" enthält, zusätzlich:
- `task_projects` — Alle Projekte mit Counts
- `task_tags` — Alle aktiven Tags
- Top 5 Tasks nach Dringlichkeit

## Format

Kompakter, übersichtlicher Output. Antworte auf Deutsch.
Nutze Emojis sparsam für Status-Anzeige (✓ synced, ⚠ überfällig, ▶ aktiv).
