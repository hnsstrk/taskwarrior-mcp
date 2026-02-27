---
description: "Taskwarrior task management. Use when the user discusses tasks, todos, deadlines, project planning, reviews, or needs help organizing and prioritizing work."
---

# Taskwarrior Integration

## MCP Tools (Server: taskwarrior)

### Lesen
- `task_list(filter_expr?, project?, tags?, status?, limit?)` — Tasks filtern und auflisten
- `task_get(uuid)` — Einzelnen Task per UUID abrufen
- `task_projects()` — Alle Projekte mit Task-Counts
- `task_tags()` — Alle verwendeten Tags
- `task_stats()` — Statistiken und Übersicht

### Schreiben
- `task_add(description, project?, priority?, due?, tags?, scheduled?, wait?, recur?)` — Task erstellen, gibt UUID zurück
- `task_modify(uuid, description?, project?, priority?, due?, tags_add?, tags_remove?, scheduled?, wait?, recur?)` — Task-Attribute ändern
- `task_done(uuid)` — Task als abgeschlossen markieren
- `task_delete(uuid)` — Task löschen (immer Bestätigung einholen!)
- `task_start(uuid)` — Task als aktiv markieren
- `task_stop(uuid)` — Aktiven Task stoppen

## Filter-Syntax (für filter_expr)

```
project:Work          # Bestimmtes Projekt
+urgent               # Tag vorhanden
-urgent               # Tag nicht vorhanden
due.before:eow        # Fällig vor Ende der Woche
status:pending        # Status (pending/completed/deleted/waiting)
priority:H            # Priorität (H/M/L)
+OVERDUE              # Überfällige Tasks (virtuelles Tag)
+TODAY                # Heute fällige Tasks
+ACTIVE               # Aktuell gestartete Tasks
+BLOCKED              # Blockierte Tasks
description.contains:meeting  # Beschreibung enthält Text
project.not:Work      # Nicht in Projekt Work
```

## Datumsformate

| Format | Bedeutung |
|--------|-----------|
| `today` | Heute |
| `tomorrow` | Morgen |
| `eow` | Ende der Woche (Sonntag) |
| `eom` | Ende des Monats |
| `eoq` | Ende des Quartals |
| `+2d` | In 2 Tagen |
| `+1w` | In 1 Woche |
| `+3m` | In 3 Monaten |
| `2025-03-15` | Exaktes Datum (ISO) |

## Prioritäten

- `H` — Hoch (High)
- `M` — Mittel (Medium)
- `L` — Niedrig (Low)

## Regeln

1. **IMMER UUIDs verwenden** — Integer-IDs ändern sich bei jeder Mutation, niemals für Schreiboperationen nutzen
2. **Vor `task_delete` Bestätigung einholen** — Destruktive Operation, immer nachfragen
3. **Sprache**: Deutsch wenn der User Deutsch spricht
4. **Tags**: Alphanumerisch mit Bindestrichen und Punkten (`[\w\-\.]+`)
5. **Neuer Task → UUID merken**: `task_add` gibt direkt das Task-Objekt mit UUID zurück

## Beispiele

```
# Alle offenen Tasks im Projekt Work
task_list(project="Work", status="pending")

# Überfällige Tasks
task_list(filter_expr="+OVERDUE")

# Task mit hoher Priorität und Deadline erstellen
task_add(description="Präsentation vorbereiten", project="Work", priority="H", due="eow", tags=["präsentation"])

# Task abschließen (mit UUID)
task_done(uuid="a1b2c3d4-...")
```
