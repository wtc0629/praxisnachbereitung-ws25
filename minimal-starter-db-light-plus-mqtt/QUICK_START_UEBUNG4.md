# Quick Start Guide - Übung 4

## 1. Services starten

```bash
cd minimal-starter-db-light-plus-mqtt
docker compose up --build
```

Warte bis alle Services laufen (ca. 30 Sekunden).

## 2. Alembic Migration ausführen

```bash
docker compose exec api alembic upgrade head
```

**Erwartete Ausgabe**:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 20251123_01, add damage_notes to assignment
```

## 3. Endpoints testen

### CSV-Export im Browser

Öffne: http://localhost:8000/assignments.csv

→ Download von `assignments.csv` startet

### XLSX-Export im Browser

Öffne: http://localhost:8000/assignments.xlsx

→ Download von `assignments.xlsx` startet

### Mit curl

```bash
# CSV
curl -o assignments.csv http://localhost:8000/assignments.csv

# XLSX
curl -o assignments.xlsx http://localhost:8000/assignments.xlsx
```

## 4. Testdaten mit Schaden anlegen

### Gerät zurückgeben mit Schadensnotiz

```bash
# Assignment 1 zurückgeben mit Schaden
curl -X POST http://localhost:8000/assignments/1/return \
  -H "Content-Type: application/json" \
  -d '{
    "damage_notes": "Display hat Kratzer, USB-C Port funktioniert nicht"
  }'
```

### Neues Assignment mit späterer Rückgabe + Schaden

```bash
# 1. Neues Assignment erstellen
curl -X POST http://localhost:8000/assignments \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 1,
    "person_id": 4,
    "notes": "Für Projekt XY"
  }'

# 2. Rückgabe mit Schaden (Assignment ID anpassen!)
curl -X POST http://localhost:8000/assignments/4/return \
  -H "Content-Type: application/json" \
  -d '{
    "damage_notes": "Akku hält nur noch 2 Stunden"
  }'
```

## 5. Excel-Auswertung

### CSV in Excel öffnen (Power Query)

1. Excel öffnen
2. **Daten** → **Aus dem Web**
3. URL: `http://localhost:8000/assignments.csv`
4. Im Power Query Editor:
   - Trennzeichen: Semikolon (sollte automatisch erkannt werden)
   - Datentypen prüfen (assigned_from, assigned_to als Datum/Uhrzeit)
5. **Schließen & Laden**

### XLSX direkt öffnen

1. `assignments.xlsx` herunterladen
2. In Excel öffnen
3. Datentypen sind bereits korrekt gesetzt

### Pivot-Auswertung erstellen

1. Beliebige Zelle in der Datentabelle anklicken
2. **Einfügen** → **PivotTable**
3. **Neue Arbeitsmappe** wählen

**Beispiel: Aktive Ausleihen pro Standort**
- Zeilen: `location_name`
- Werte: Anzahl von `assignment_id`
- Filter: `assigned_to` = (Leer)

**Beispiel: Gerätetypen-Nutzung**
- Zeilen: `device_type`
- Werte: Anzahl von `assignment_id`

**Beispiel: Schäden pro Standort**
- Zeilen: `location_name`
- Werte: Anzahl von `assignment_id`
- Filter: `damage_notes` ≠ (Leer)

## 6. API-Dokumentation ansehen

Öffne: http://localhost:8000/docs

→ Interaktive Swagger UI mit allen Endpoints

## 7. Services stoppen

```bash
docker compose down
```

## Troubleshooting

### Migration schlägt fehl

**Problem**: `relation "assignment" does not exist`

**Lösung**: Schema muss zuerst initialisiert werden
```bash
# DB neu aufsetzen
docker compose down -v
docker compose up -d db
# Warten bis DB bereit
docker compose up -d
docker compose exec api alembic upgrade head
```

### CSV zeigt falsche Zeichen in Excel

**Ursache**: Excel erkennt UTF-8 nicht

**Lösung**: CSV ist bereits mit UTF-8 BOM encoded. Falls Probleme auftreten:
- Power Query verwenden statt direktes Öffnen
- Oder: Excel → Daten → Aus Text/CSV → Encoding: UTF-8

### XLSX kann nicht geöffnet werden

**Ursache**: pandas/openpyxl nicht installiert

**Lösung**: `requirements.txt` aktualisiert, neu builden:
```bash
docker compose up --build
```

## Nützliche Links

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- CSV Export: http://localhost:8000/assignments.csv
- XLSX Export: http://localhost:8000/assignments.xlsx
- Alle Assignments (JSON): http://localhost:8000/assignments
