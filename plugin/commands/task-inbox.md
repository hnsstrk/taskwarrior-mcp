---
description: "GTD inbox processing for untagged and unassigned tasks"
disable-model-invocation: true
---

# GTD Inbox Processing

Verarbeite alle Tasks ohne Projekt oder Kategorisierung (Inbox-Clearing nach GTD).

## Argumente

$ARGUMENTS (optional: zusätzlicher Filter oder Projektname als Ziel)

## GTD Inbox-Verarbeitung

### 1. Inbox identifizieren
Finde alle Tasks die noch nicht kategorisiert sind:
- `task_list` mit `filter_expr="project: status:pending $ARGUMENTS"` — Tasks ohne Projekt
- `task_list` mit `filter_expr="priority: status:pending $ARGUMENTS"` — Tasks ohne Priorität
- Zeige die Gesamtanzahl

### 2. Jeden Task durchgehen
Für jeden unkategorisierten Task:

**Entscheidungsbaum (GTD):**
1. **Ist es umsetzbar?**
   - Nein → Löschen (`task_delete`) oder als Referenz behalten (Tag: `+referenz`)
   - Ja → Weiter zu Schritt 2

2. **Dauert es < 2 Minuten?**
   - Ja → Sofort erledigen und `task_done` aufrufen
   - Nein → Weiter zu Schritt 3

3. **Einordnen:**
   - Projekt zuweisen (`project:XYZ`)
   - Priorität setzen (`priority:H/M/L`)
   - Fälligkeitsdatum wenn relevant (`due:...`)
   - Tags für Kontext (`+@home`, `+@office`, `+@computer`)
   - Warten auf jemanden? → `+waiting` Tag und `wait:` Datum

### 3. Interaktiv verarbeiten
Gehe die Tasks durch und schlage für jeden vor:
- Empfohlenes Projekt (basierend auf ähnlichen Tasks)
- Empfohlene Priorität
- Ob ein Fälligkeitsdatum sinnvoll ist

Warte auf Bestätigung oder Anpassung bevor `task_modify` aufgerufen wird.

### 4. Abschlussbericht
Nach der Verarbeitung:
- Wie viele Tasks wurden kategorisiert?
- Wie viele wurden erledigt oder gelöscht?
- Verbleibende Inbox-Tasks?
- Übersicht der neuen/geänderten Projekte

## Regeln

- **Nie ohne Bestätigung ändern** — Zeige Vorschlag, warte auf OK
- **Batching möglich** — Bei gleicher Kategorisierung mehrere Tasks auf einmal
- Antworte auf Deutsch
