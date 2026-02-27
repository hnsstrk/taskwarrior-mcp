---
description: "Weekly planning session with project overview and priority setting"
disable-model-invocation: true
---

# Wochenplanung

Erstelle eine strukturierte Wochenplanung basierend auf offenen Tasks.

## Argumente

$ARGUMENTS (optional: Projekt oder Filter, z.B. "project:Work" oder "next week")

## Ablauf

### 1. Aktuelle Situation analysieren
- `task_list` mit `filter_expr="status:pending $ARGUMENTS"` und `limit=100`
- `task_projects` — Alle Projekte und deren Umfang
- `task_stats` — Gesamtstatistik

### 2. Prioritäten dieser Woche
Identifiziere Tasks die diese Woche erledigt werden müssen:
- `task_list` mit `filter_expr="due.before:eow $ARGUMENTS"`
- `task_list` mit `filter_expr="priority:H $ARGUMENTS"`
- `task_list` mit `filter_expr="+OVERDUE $ARGUMENTS"`

### 3. Wochenplan erstellen
Erstelle einen strukturierten Plan für die Woche (Mo-Fr):
- Verteile Tasks sinnvoll auf die Wochentage
- Berücksichtige Abhängigkeiten und Deadlines
- Plane Buffer für unvorhergesehenes ein
- Priorisiere: Überfällig → Heute fällig → Hohe Priorität → Normale Tasks

### 4. Empfehlungen
- Welche Tasks können diese Woche realistisch abgeschlossen werden?
- Welche Tasks sollten verschoben oder delegiert werden?
- Gibt es Abhängigkeiten zwischen Tasks (`+BLOCKED`)?
- Vorschlag: Welche neuen Tags/Projekte würden die Organisation verbessern?

### 5. Nächste Schritte
Liste die 3-5 wichtigsten Tasks auf die sofort begonnen werden sollten.
Optional: Frage ob Tasks direkt über `task_start` als aktiv markiert werden sollen.

## Format

Antworte auf Deutsch. Strukturiere den Wochenplan als klare Tabelle oder Liste.
Sei realistisch bei der Zeitplanung.
