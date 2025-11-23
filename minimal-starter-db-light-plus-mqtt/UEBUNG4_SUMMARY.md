# Übung 4 - Inventar-App Datenbereitstellung & Auswertung

## Zusammenfassung der Implementierung

Alle Anforderungen aus Übung 4 wurden erfolgreich umgesetzt:

### ✅ A) Schemaänderung mit Alembic - Schaden-Vermerk

**Fachliche Begründung:**
Bei der Rückgabe eines Geräts muss dokumentiert werden können, ob das Gerät beschädigt wurde.

**Technische Umsetzung:**
- **Feld:** `damage_notes`
- **Typ:** TEXT (flexible Länge für detaillierte Schadensbeschreibungen)
- **Optionalität:** NULL erlaubt, da nicht bei jeder Rückgabe ein Schaden vorliegt
- **Migration:** `backend/migrations/versions/20251123_01_add_damage_notes_to_assignment.py`
- **Status:** ✅ Migration erfolgreich ausgeführt

**Überlegungen:**
- Name: `damage_notes` (englisch, konsistent mit `notes`)
- Platzierung: in `assignment` Tabelle, da Schäden bei Rückgabe erfasst werden
- Optionalität: NULL erlaubt, da das Feld nur bei Rückgabe mit Schaden gefüllt wird

### ✅ B) Assignment-Exports per HTTP

Beide Export-Endpunkte sind vollständig implementiert und funktionsfähig:

#### 1. GET /assignments.csv
- **Format:** CSV mit Semikolon als Trennzeichen (;)
- **Encoding:** UTF-8 mit BOM (Excel-kompatibel)
- **Spalten:**
  - assignment_id
  - inventory_no
  - serial_number
  - device_type (Name des Gerätetyps)
  - location_name (Standort)
  - person_name (Name der Person)
  - person_email (E-Mail der Person)
  - assigned_from (Ausgabedatum)
  - assigned_to (Rückgabedatum, leer = aktiv)
  - notes (Notizen zur Ausleihe)
  - damage_notes (Schadensnotizen bei Rückgabe)

**SQL-Abfrage:** JOINs über device → device_type, location und person

#### 2. GET /assignments.xlsx
- **Format:** Excel 2007+ (XLSX)
- **Engine:** pandas + openpyxl
- **Vorteile:**
  - Datentypen bleiben erhalten (Datum/Uhrzeit)
  - Direktes Öffnen in Excel ohne Import-Dialog
  - Bessere Formatierung

**Unterschied CSV vs. XLSX:**
- **CSV:** Universell, Text-basiert, für Power Query perfekt, aber Datentypen müssen neu gesetzt werden
- **XLSX:** Native Excel-Format, Datentypen bleiben erhalten, größere Dateien

### ✅ C) Excel-Pipeline mit Power Query (Anleitung)

**Variante 1 - CSV mit Power Query (empfohlen für laufende Auswertungen):**
1. Excel → Daten → Aus dem Web
2. URL: `http://localhost:8000/assignments.csv`
3. Trennzeichen wird automatisch erkannt (;)
4. Datentypen in Power Query anpassen
5. Vorteil: Immer aktuelle Daten per "Aktualisieren"

**Variante 2 - XLSX-Datei (empfohlen für Snapshots):**
1. XLSX-Datei herunterladen
2. Direkt in Excel öffnen
3. Datentypen sind bereits korrekt
4. Vorteil: Monatliche Reports, Archivierung

**Empfehlung für Fachbereiche:**
- **Laufende Auswertungen:** CSV + Power Query (immer aktuell)
- **Monatliche Reports:** XLSX-Download (fester Zeitpunkt)
- **Ad-hoc Analysen:** XLSX-Download (schnell & einfach)

### ✅ D) Pivot-Auswertungen (Beispiele)

#### Pivot 1: Aktive Ausleihen pro Standort
```
Zeilen: location_name
Werte: Anzahl von assignment_id
Filter: assigned_to = (Leer)
```
**Beantwortet:** "Welche Standorte haben aktuell die meisten Geräte im Einsatz?"

#### Pivot 2: Nutzung pro DeviceType
```
Zeilen: device_type
Werte: Anzahl von assignment_id
```
**Beantwortet:** "Welche Gerätetypen werden am häufigsten ausgeliehen?"

#### Pivot 3: Geräte pro Person
```
Zeilen: person_name
Werte: Anzahl von assignment_id
Filter: assigned_to = (Leer)
```
**Beantwortet:** "Wer hat aktuell wie viele Geräte im Einsatz?"

#### Pivot 4: Schäden pro Standort
```
Zeilen: location_name
Werte: Anzahl von assignment_id
Filter: damage_notes ≠ (Leer)
```
**Beantwortet:** "Welche Standorte haben die meisten Schäden gemeldet?"

## Technische Details

### API-Endpoints

```bash
# Gesundheitscheck
http://localhost:8000/health

# Alle Assignments (JSON)
http://localhost:8000/assignments

# CSV-Export
http://localhost:8000/assignments.csv

# XLSX-Export
http://localhost:8000/assignments.xlsx

# API-Dokumentation (Swagger)
http://localhost:8000/docs
```

### Beispiel: Rückgabe mit Schaden

```bash
curl -X POST http://localhost:8000/assignments/1/return \
  -H "Content-Type: application/json" \
  -d '{
    "damage_notes": "Display has scratches, USB-C port is loose"
  }'
```

### Migration ausführen

```bash
# Services starten
docker compose up -d

# Migration ausführen
docker compose exec api alembic upgrade head

# Migration zurückrollen (falls nötig)
docker compose exec api alembic downgrade -1
```

## Testdaten

Aktuell im System:
- 3 aktive Assignments
- 1 zurückgegebenes Assignment mit Schaden
- Verschiedene Gerätetypen: Laptop, Monitor, Tablet
- Mehrere Standorte: Remote/Homeoffice, Labor

## Demo-Ablauf für Präsentation

### 1. API-Exports zeigen (2 Min)
```bash
# Browser öffnen:
# - http://localhost:8000/assignments.csv (Download)
# - http://localhost:8000/assignments.xlsx (Download)

# Oder mit curl:
curl -o assignments.csv http://localhost:8000/assignments.csv
curl -o assignments.xlsx http://localhost:8000/assignments.xlsx
```

**Erklärung:**
"Die Assignment-Sicht verbindet via SQL-JOINs die Tabellen assignment, device, device_type, location und person. So erhalten Fachbereiche alle relevanten Informationen in einer Datei."

### 2. Excel-Auswertungen zeigen (3 Min)
- Eine Excel-Datei mit Power Query-Anbindung öffnen
- 2-3 Pivot-Tabellen präsentieren
- Praktische Fragestellungen erläutern

### 3. Schaden-Vermerk demonstrieren (2 Min)
```bash
# Rückgabe mit Schaden
curl -X POST http://localhost:8000/assignments/2/return \
  -H "Content-Type: application/json" \
  -d '{"damage_notes": "Akku hält nur noch 2 Stunden"}'

# CSV neu laden - Schaden ist sichtbar
curl http://localhost:8000/assignments.csv
```

**Erklärung:**
"Das Feld damage_notes wurde via Alembic-Migration hinzugefügt. Es ist optional (NULL), da nicht jede Rückgabe einen Schaden hat. Die Migration ist versioniert und kann zurückgerollt werden."

### 4. Reflexion (2 Min)

**Was lief gut:**
- Alembic-Migration funktioniert reibungslos
- CSV/XLSX-Export mit korrekten Datentypen
- SQL-JOINs liefern aussagekräftige Daten
- Power Query ermöglicht Live-Updates

**Stolpersteine:**
- Alembic-Konfiguration benötigte Anpassung für psycopg (statt psycopg2)
- UTF-8 BOM wichtig für Excel-Kompatibilität bei CSV

**Empfehlung für echtes Projekt:**
- **CSV + Power Query** für laufende Auswertungen (immer aktuell, automatisierbar)
- **XLSX** für monatliche Reports und Archivierung (fester Zeitpunkt, Datentypen erhalten)
- Kombination beider Ansätze je nach Use Case

## Nächste Schritte

Für Produktiv-Betrieb:
1. Authentifizierung hinzufügen (API-Keys, OAuth)
2. Pagination für große Datenmengen
3. Filter-Parameter (z.B. Zeitraum, Standort)
4. Scheduled Exports (z.B. nächtlicher Report)
5. Benachrichtigungen bei Schäden (E-Mail, MQTT)

## Verwendete Technologien

- **Backend:** FastAPI (Python)
- **Datenbank:** PostgreSQL 16
- **Migration:** Alembic 1.13.1
- **Export:**
  - CSV: Python csv + io.StringIO
  - XLSX: pandas 2.2.0 + openpyxl 3.1.2
- **Frontend:** Excel + Power Query
- **Container:** Docker Compose

---

**Status:** ✅ Alle Anforderungen erfüllt und getestet
**Branch:** feat/tag4-inventar-export
**Datum:** 2025-11-23
