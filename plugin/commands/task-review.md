---
description: "Structured daily task review with overdue, today, and upcoming tasks"
disable-model-invocation: true
---

# Tägliche Task-Review

Führe eine strukturierte tägliche Task-Review durch.

## Argumente

$ARGUMENTS (optional: Projektfilter, z.B. "project:Work")

## Ablauf

Führe folgende Schritte durch und präsentiere die Ergebnisse übersichtlich:

### 1. Überfällige Tasks
Zeige alle überfälligen Tasks:
- Nutze `task_list` mit `filter_expr="+OVERDUE $ARGUMENTS"`
- Falls Tasks gefunden: zeige sie mit Priorität, Projekt und Fälligkeitsdatum

### 2. Heute fällige Tasks
- Nutze `task_list` mit `filter_expr="+TODAY $ARGUMENTS"`
- Hebe hohe Priorität besonders hervor

### 3. Aktive Tasks (gestartet)
- Nutze `task_list` mit `filter_expr="+ACTIVE $ARGUMENTS"`
- Zeige seit wann der Task aktiv ist

### 4. Nächste Aufgaben (diese Woche)
- Nutze `task_list` mit `filter_expr="due.before:eow $ARGUMENTS status:pending"`
- Sortiert nach Priorität und Fälligkeitsdatum

### 5. Kurzstatistik
- Rufe `task_stats` auf
- Zeige: Gesamt offen, heute fällig, überfällig, abgeschlossen diese Woche

### 6. Empfehlungen
Basierend auf den Daten:
- Was sollte heute unbedingt erledigt werden?
- Gibt es Tasks die delegiert oder verschoben werden sollten?
- Sind Tasks ohne Projekt oder Priorität vorhanden die strukturiert werden sollten?

## Format

Antworte auf Deutsch. Nutze Markdown-Tabellen für Task-Listen.
Fasse am Ende in 2-3 Sätzen zusammen was der Fokus des Tages sein sollte.
