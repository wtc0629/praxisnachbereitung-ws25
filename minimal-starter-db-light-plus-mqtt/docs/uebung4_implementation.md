# Übung 4: Inventar-App – Implementierung

## Übersicht

Diese Dokumentation beschreibt die Implementierung von Übung 4, bei der die Inventar-App um folgende Features erweitert wurde:

1. **Schemaänderung mit Alembic**: Hinzufügen eines `damage_notes` Feldes zur Assignment-Tabelle
2. **Assignment-Exports**: HTTP-Endpoints für CSV und XLSX Export
3. **Excel-Integration**: Vorbereitung für Power Query Anbindung

## A) Schemaänderung mit Alembic – damage_notes Feld

### Fachliche Begründung

**Warum brauchen wir das damage_notes Feld?**

Bei der Rückgabe von Geräten ist es wichtig, dokumentieren zu können, ob und welche Schäden am Gerät aufgetreten sind. Dies ermöglicht:
- Nachvollziehbarkeit von Geräteschäden
- Verantwortungszuordnung
- Wartungs- und Reparaturplanung
- Statistische Auswertung zur Gerätequalität

### Technische Überlegungen

**Attribut-Design:**
- **Name**: `damage_notes` (englisch, konsistent mit bestehendem `notes` Feld)
- **Typ**: TEXT (PostgreSQL) - ermöglicht flexible Länge für detaillierte Schadensbeschreibungen
- **Optionalität**: NULL erlaubt - das Feld wird nur gefüllt, wenn tatsächlich ein Schaden vorliegt
- **Platzierung**: in `assignment` Tabelle, da Schäden bei Rückgabe erfasst werden

### Implementierung

**Migration erstellt**: `backend/migrations/versions/20251123_01_add_damage_notes_to_assignment.py`

```python
def upgrade() -> None:
    op.add_column('assignment', sa.Column('damage_notes', sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column('assignment', 'damage_notes')
```

**Migration ausführen:**

```bash
# Im Container
docker compose exec api alembic upgrade head

# Lokal (falls Alembic lokal installiert)
cd minimal-starter-db-light-plus-mqtt
alembic upgrade head
```

**Migration prüfen:**

```sql
-- In psql oder DB-Tool
\d assignment
-- Sollte die neue Spalte "damage_notes | text" anzeigen
```

### Modell-Updates

**Assignment Model** (`backend/app/models.py`):
- `Assignment`: `damage_notes: Optional[str] = None` hinzugefügt
- `AssignmentReturn`: `damage_notes: Optional[str] = None` hinzugefügt

**API-Endpoint Update**:
- `POST /assignments/{assignment_id}/return` akzeptiert jetzt `damage_notes` im Request Body

## B) Assignment-Exports per HTTP

### Spalten der Assignment-Sicht

Die Export-Endpoints liefern eine denormalisierte Sicht auf Assignments mit allen relevanten Informationen:

| Spalte | Beschreibung |
|--------|--------------|
| assignment_id | Eindeutige ID der Ausleihe |
| inventory_no | Inventarnummer des Geräts |
| serial_number | Seriennummer (hier = inventory_no) |
| device_type | Name des Gerätetyps (z.B. "Laptop") |
| location_name | Standortname (z.B. "Headquarters") |
| person_name | Name der Person |
| person_email | E-Mail der Person |
| assigned_from | Ausgabedatum |
| assigned_to | Rückgabedatum (NULL = aktiv) |
| notes | Allgemeine Notizen zur Ausleihe |
| damage_notes | Schadensnotizen bei Rückgabe |

### SQL-Join für Assignment-Sicht

```sql
select
    a.assignment_id,
    d.inventory_no,
    d.inventory_no as serial_number,
    dt.name as device_type,
    l.name as location_name,
    p.name as person_name,
    p.email as person_email,
    a.assigned_from,
    a.assigned_to,
    a.notes,
    a.damage_notes
from assignment a
join device d on d.device_id = a.device_id
join device_type dt on dt.device_type_id = d.device_type_id
join location l on l.location_id = d.location_id
join person p on p.person_id = a.person_id
order by a.assigned_from desc
```

### Endpoints

#### GET /assignments.csv

**Beschreibung**: Exportiert alle Assignments als CSV-Datei

**Features**:
- Trennzeichen: `;` (Semikolon)
- Encoding: UTF-8 mit BOM (utf-8-sig) für Excel-Kompatibilität
- Header-Zeile enthalten
- Content-Disposition: attachment mit Dateiname "assignments.csv"

**Beispiel-Aufruf**:
```bash
curl -o assignments.csv http://localhost:8000/assignments.csv
```

**Browser**: Einfach `http://localhost:8000/assignments.csv` aufrufen → Download startet

#### GET /assignments.xlsx

**Beschreibung**: Exportiert alle Assignments als Excel-Datei (XLSX)

**Features**:
- Verwendet Pandas + openpyxl für native Excel-Format
- Datentypen werden korrekt in Excel dargestellt
- Sheet-Name: "Assignments"
- Kein Index (index=False)

**Beispiel-Aufruf**:
```bash
curl -o assignments.xlsx http://localhost:8000/assignments.xlsx
```

**Browser**: Einfach `http://localhost:8000/assignments.xlsx` aufrufen → Download startet

### CSV vs. XLSX – Unterschiede in der Nutzung

**CSV-Vorteile**:
- Kleinere Dateigröße
- Universell lesbar (Text-Editor, Excel, Google Sheets, etc.)
- Einfaches Parsing in Scripts
- Schneller Export
- Gut für automatisierte Pipelines (z.B. Power Query mit URL)

**XLSX-Vorteile**:
- Behält Datentypen (Datum, Zahl, Text)
- Bessere Excel-Integration (kein Importassistent nötig)
- Unterstützt Formatierung
- Mehrere Sheets möglich (hier noch nicht genutzt)
- Besser für einmalige Downloads/Snapshots

**Empfehlung**:
- **CSV mit URL**: Für regelmäßig aktualisierte Power Query Dashboards
- **XLSX-Datei**: Für monatliche Snapshots oder Ad-hoc-Analysen

## C) Excel-Pipeline mit Power Query

### Variante 1: Power Query mit CSV-URL

**Anwendungsfall**: Live-Datenanbindung für immer aktuelle Dashboards

**Setup in Excel**:
1. Daten → Aus dem Web
2. URL eingeben: `http://localhost:8000/assignments.csv`
3. Trennzeichen: Semikolon (`;`)
4. Datentypen prüfen und anpassen:
   - `assigned_from`: Datum/Uhrzeit
   - `assigned_to`: Datum/Uhrzeit
   - `assignment_id`: Ganze Zahl
5. Query benennen: "AssignmentFromAPI"
6. In Excel laden

**Aktualisierung**: Daten → Alle aktualisieren

**Vorteile**:
- Immer aktuelle Daten
- Ein Klick zum Aktualisieren
- Zentrale Datenhaltung

**Nachteile**:
- API muss erreichbar sein
- Langsamer bei vielen Daten

### Variante 2: Power Query mit XLSX-Datei

**Anwendungsfall**: Statische Snapshots für Archivierung oder Offline-Analysen

**Setup in Excel**:
1. XLSX-Datei herunterladen: `http://localhost:8000/assignments.xlsx`
2. Neue Arbeitsmappe erstellen
3. Daten → Aus Arbeitsmappe
4. Heruntergeladene `assignments.xlsx` auswählen
5. Sheet "Assignments" importieren
6. Datentypen sind bereits korrekt gesetzt

**Vorteile**:
- Offline verfügbar
- Schneller
- Snapshot-Archivierung (z.B. "assignments_2025-01.xlsx")

**Nachteile**:
- Manuelle Aktualisierung nötig
- Datei muss neu heruntergeladen werden

## D) Pivot-Auswertungen (Beispiele)

### 1. Aktive Ausleihen pro Standort

**Definition "aktiv"**: `assigned_to` ist leer/NULL

**Pivot-Setup**:
- Zeilen: `location_name`
- Werte: Anzahl von `assignment_id`
- Filter: `assigned_to` = (Leer)

**Ergebnis**: Zeigt, wie viele Geräte aktuell an welchem Standort aktiv ausgeliehen sind

### 2. Nutzung pro DeviceType

**Pivot-Setup**:
- Zeilen: `device_type`
- Werte: Anzahl von `assignment_id`
- Optional Filter: `assigned_from` >= 2025-01-01 (letzte 12 Monate)

**Ergebnis**: Welche Gerätetypen werden am häufigsten ausgeliehen?

### 3. Geräte pro Person

**Pivot-Setup**:
- Zeilen: `person_name`
- Werte: Anzahl von `assignment_id`
- Filter: `assigned_to` = (Leer)

**Ergebnis**: Wer hat aktuell wie viele Geräte im Einsatz?

### 4. Schäden pro Standort (optional)

**Pivot-Setup**:
- Zeilen: `location_name`
- Werte: Anzahl von `assignment_id`
- Filter: `damage_notes` <> (Leer)

**Ergebnis**: An welchen Standorten treten die meisten Schäden auf?

**Geschäftsfrage**: Gibt es Standorte mit besonders hoher Schadensrate? → Schulungsbedarf oder Equipment-Qualität prüfen

## E) Testing & Demo

### 1. Docker Services starten

```bash
cd minimal-starter-db-light-plus-mqtt
docker compose up --build
```

### 2. Alembic Migration ausführen

```bash
docker compose exec api alembic upgrade head
```

### 3. Endpoints testen

**CSV-Export**:
```bash
curl http://localhost:8000/assignments.csv
```

**XLSX-Export**:
```bash
curl -o test_assignments.xlsx http://localhost:8000/assignments.xlsx
```

**Browser**:
- http://localhost:8000/assignments.csv
- http://localhost:8000/assignments.xlsx

### 4. Testdaten mit damage_notes anlegen

**Assignment mit Schaden zurückgeben**:

```bash
curl -X POST http://localhost:8000/assignments/1/return \
  -H "Content-Type: application/json" \
  -d '{
    "assigned_to": "2025-11-23T15:30:00",
    "damage_notes": "Display hat Kratzer, USB-C Port funktioniert nicht"
  }'
```

### 5. Excel-Dateien öffnen

1. `assignments.xlsx` in Excel öffnen
2. Pivot-Tabelle erstellen (Einfügen → PivotTable)
3. Auswertungen wie oben beschrieben durchführen

## Zusammenfassung

### Was wurde implementiert?

✅ Alembic Setup für Datenbank-Migrationen
✅ Migration für `damage_notes` Feld in Assignment-Tabelle
✅ API-Modelle erweitert (Assignment, AssignmentReturn)
✅ GET /assignments.csv Endpoint (Semikolon-getrennt, UTF-8 BOM)
✅ GET /assignments.xlsx Endpoint (Pandas + openpyxl)
✅ Docker-Setup angepasst für Alembic
✅ Dokumentation der Implementierung

### Nächste Schritte (für Präsentation)

1. **Demo vorbereiten**:
   - Docker Compose starten
   - Migration ausführen
   - Testdaten mit Schäden anlegen
   - Beide Endpoints aufrufen

2. **Excel-Pivot vorbereiten**:
   - 2-3 Pivot-Auswertungen in Excel erstellen
   - Screenshots für Präsentation

3. **Reflexion vorbereiten**:
   - CSV vs. XLSX Vor-/Nachteile
   - Stolpersteine (z.B. UTF-8 BOM für Excel, Datum-Formatierung)
   - Empfehlung für echtes Projekt

## Anhang: Nützliche Befehle

```bash
# Alembic: Neue Migration erstellen
alembic revision -m "beschreibung"

# Alembic: Migration ausführen
alembic upgrade head

# Alembic: Migration rückgängig machen
alembic downgrade -1

# Alembic: Status zeigen
alembic current

# Alembic: Historie zeigen
alembic history
```
