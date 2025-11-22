# Grades-Starter Analyse

**Datum**: 2025-11-22
**Zweck**: Verstehen des g_starter als Blaupause für die Inventar-App (Übung 3)

---

## 1. Überblick

Der Grades-Starter ist eine Demo-App für die Verwaltung von **Studenten, Modulen und Noten** mit:
- FastAPI (Backend)
- PostgreSQL (Datenbank)
- MQTT (Eclipse Mosquitto)
- Einfacher HTML-UI mit Jinja2 + htmx
- CSV-Export-Funktionalität

---

## 2. Datenmodell (Tabellen + Beziehungen)

### Tabellen

| Tabelle | Primärschlüssel | Wichtige Felder | Constraints |
|---------|-----------------|-----------------|-------------|
| `student` | `student_id` (SERIAL) | `matrikel` (UNIQUE), `vorname`, `nachname`, `programme`, `semester` | CHECK: `semester BETWEEN 1 AND 12` |
| `module` | `module_id` (SERIAL) | `name` (UNIQUE) | - |
| `grade` | `grade_id` (SERIAL) | `student_id` (FK), `module_id` (FK), `grade_value`, `graded_at` | ON DELETE CASCADE |

### Beziehungen

```
student (1) ----< (N) grade (N) >---- (1) module
```

- **student → grade**: 1:N (Ein Student kann viele Noten haben)
- **module → grade**: 1:N (Ein Modul kann viele Noten haben)
- **grade**: Verbindungstabelle mit zusätzlichen Feldern (`grade_value`, `graded_at`)

### Constraints im Detail

**student**:
```sql
matrikel text not null unique
semester int not null check (semester between 1 and 12)
```

**module**:
```sql
name text not null unique
```

**grade**:
```sql
student_id int not null references student(student_id) on delete cascade
module_id int not null references module(module_id) on delete cascade
```

### Seed-Daten

- 3 Studenten (Anna Koch, Ben König, Clara Meier)
- 4 Module (Datenbanken, Programmierung 1, Software Engineering, Mathematik 1)
- 5 Noten (verschiedene Kombinationen)

Verwendung von `ON CONFLICT DO NOTHING` für Idempotenz.

---

## 3. Projekt-Struktur

```
g_starter/
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── db.py                      # DB-Verbindung
│       ├── main.py                    # FastAPI App + Routen
│       ├── models.py                  # Pydantic Modelle
│       ├── mqtt_integration.py        # MQTT Subscriber
│       └── templates/
│           ├── index.html             # Startseite
│           ├── grades/
│           │   ├── index.html         # Noten-UI mit htmx
│           │   └── _list.html         # Partial Template
│           └── students/
│               ├── index.html         # Studenten-Liste
│               └── edit.html          # Bearbeiten-Formular
├── db/
│   └── init/
│       └── 001_schema.sql             # Schema + Seed-Daten
├── mqtt/
│   └── mosquitto.conf                 # MQTT Broker Config
├── docker-compose.yml                 # 3 Services: db, mqtt, api
├── Dockerfile                         # Python App Container
├── requirements.txt                   # Dependencies
└── README.md
```

---

## 4. Wichtige Code-Teile für Inventar-Wiederverwendung

### A) DB-Zugriff (`backend/app/db.py`)

**Pattern**:
```python
import psycopg
from psycopg.rows import dict_row

def get_conn():
    dsn = os.getenv("DB_DSN", "postgresql://appuser:apppass@db:5432/appdb")
    return psycopg.connect(dsn, autocommit=True, row_factory=dict_row)
```

**Vorteile**:
- `dict_row`: Zeilen als Dictionaries → leichter Zugriff
- `autocommit=True`: Keine manuellen Commits nötig
- Environment Variable für DSN

**Für Inventar**: 1:1 übernehmen

---

### B) Pydantic Modelle (`backend/app/models.py`)

**Pattern**:
```python
from pydantic import BaseModel
from typing import Optional

class Student(BaseModel):
    student_id: int
    matrikel: str
    vorname: str
    nachname: str
    programme: str
    semester: int

class StudentCreate(BaseModel):
    matrikel: str
    vorname: str
    nachname: str
    programme: str
    semester: int

class StudentUpdate(BaseModel):
    vorname: Optional[str] = None
    nachname: Optional[str] = None
    # ... weitere optionale Felder
```

**Für Inventar**:
- Erstelle ähnliche Modelle für `Device`, `Person`, `Assignment`
- Trenne Base-Modell, Create-Modell, Update-Modell

---

### C) API-Routen (`backend/app/main.py`)

**Typische Route-Struktur**:
```python
@app.post("/students", status_code=201)
async def create_student(student: StudentCreate):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            insert into student (matrikel, vorname, nachname, programme, semester)
            values (%s, %s, %s, %s, %s)
            returning *
        """, (student.matrikel, student.vorname, student.nachname,
              student.programme, student.semester))
        new_student = cur.fetchone()
    return new_student
```

**Fehlerbehandlung**:
- Keine explizite Fehlerbehandlung in diesem Beispiel
- Für Inventar: Hinzufügen von `HTTPException` für Domain-Regeln

**Für Inventar**:
- Übernehme Pattern
- Füge Domain-Regel-Validierung hinzu (IR-01, IR-02, IR-03)

---

### D) Templates mit htmx (`backend/app/templates/`)

**Struktur**:
- `index.html`: Hauptseite mit Links
- `grades/index.html`: Vollständige Seite
- `grades/_list.html`: Partial für htmx-Updates

**htmx Pattern (grades/index.html)**:
```html
<select id="student-select"
        hx-get="/grades/for-student"
        hx-target="#grades-list"
        hx-swap="innerHTML">
  <option value="">Wähle Student...</option>
</select>

<div id="grades-list">
  <!-- Wird durch htmx aktualisiert -->
</div>
```

**Vorteile**:
- Dynamische Updates ohne JavaScript
- Einfache AJAX-Requests
- Progressive Enhancement

**Für Inventar**:
- Optional: Verwende htmx für dynamische Device-Liste
- Oder nutze einfaches JavaScript (wie in aktueller Lösung)

---

### E) MQTT Integration (`backend/app/mqtt_integration.py`)

**Subscriber Pattern**:
```python
import paho.mqtt.client as mqtt
import json
from threading import Thread

def on_connect(client, userdata, flags, rc):
    client.subscribe("grades/new")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        # Insert into database
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                insert into grade (student_id, module_id, grade_value)
                values (%s, %s, %s)
            """, (payload["student_id"], payload["module_id"],
                  payload["grade_value"]))
    except Exception as e:
        print(f"Error: {e}")

def start_mqtt_subscriber():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("mqtt", 1883, 60)
    client.loop_forever()

# Start in background thread
Thread(target=start_mqtt_subscriber, daemon=True).start()
```

**Für Inventar**:
- **Publisher**: Verwende in API-Endpunkten (wie bereits implementiert)
- **Subscriber**: Optional, nicht für Übung 3 erforderlich

---

### F) Docker Compose Setup

**Services**:
1. `db`: PostgreSQL mit Volume-Mount für Init-SQL
2. `mqtt`: Eclipse Mosquitto mit Config
3. `api`: FastAPI App mit Dependencies

**Wichtige Konfiguration**:
```yaml
services:
  db:
    volumes:
      - ./db/init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "appuser"]

  api:
    depends_on:
      db:
        condition: service_healthy
    environment:
      DB_DSN: postgresql://appuser:apppass@db:5432/appdb
```

**Für Inventar**: Bereits korrekt übernommen

---

## 5. Wiederverwendbare Patterns für Inventar

### ✅ Was wir übernommen haben:

1. **DB-Zugriff**: `db.py` mit `dict_row` und `autocommit`
2. **Pydantic Modelle**: Trennung von Base/Create/Update
3. **API-Routen**: FastAPI mit GET/POST Endpunkten
4. **Docker Setup**: 3-Service-Architektur
5. **Init-SQL**: Idempotente Schema-Erstellung mit `ON CONFLICT`

### ✅ Was wir angepasst haben:

1. **Domain-Regeln**: Hinzugefügt IR-01, IR-02, IR-03 Validierung
2. **MQTT**: Publisher statt Subscriber (für Assignment-Events)
3. **UI**: Vollständige JavaScript-App statt htmx
4. **Fehlerbehandlung**: Explizite `HTTPException` mit Status Codes

### 📋 Was wir gelernt haben:

- **Constraint-Patterns**: UNIQUE, CHECK, FK mit ON DELETE
- **Seed-Daten**: Verwendung von `ON CONFLICT DO NOTHING`
- **Connection-Pattern**: Context Manager mit `with get_conn()`
- **Pydantic-Validation**: Automatische Request-Validierung
- **MQTT-Integration**: Publisher/Subscriber mit paho-mqtt

---

## 6. Unterschiede: Grades vs. Inventar

| Aspekt | Grades-Starter | Inventar-App |
|--------|----------------|--------------|
| **Domäne** | Student-Module-Grade | Device-Person-Assignment |
| **Haupttabellen** | 3 (student, module, grade) | 5 (person, device_type, location, device, assignment) |
| **UK-Constraints** | `matrikel`, `module.name` | `personnel_no`, `inventory_no`, `serial_number`, `device_type.code`, `location.code` |
| **Domain-Regeln** | Nur DB-Constraints | IR-01, IR-02, IR-03 (App-Level) |
| **MQTT** | Subscriber (empfängt Noten) | Publisher (sendet Events) |
| **UI** | htmx (HTML-Partial) | JavaScript (fetch API) |
| **Temporale Daten** | `graded_at` (nur Erstellungszeit) | `assigned_from`, `assigned_to` (Zeitraum) |

---

## 7. Empfehlungen für zukünftige Projekte

### Do's ✅
- Nutze `dict_row` für einfachen Dictionary-Zugriff
- Trenne Pydantic-Modelle (Base/Create/Update)
- Verwende `ON CONFLICT DO NOTHING` für Idempotenz
- Implementiere Health-Checks in Docker Compose
- Nutze Environment Variables für Konfiguration

### Don'ts ❌
- Keine hardcodierten Credentials
- Nicht alle Fehler schlucken (wie im MQTT-Beispiel)
- Keine SQL-Injection-Anfälligkeit (immer Parameterized Queries)
- Nicht ohne Validierung direkt in DB schreiben

---

## 8. Nützliche Code-Snippets

### Idempotente Insert mit JOIN (für Seed-Daten)
```sql
insert into grade (student_id, module_id, grade_value)
select s.student_id, m.module_id, g.grade_value
from (values
  ('12345', 'Datenbanken', '1,7'),
  ('23456', 'Datenbanken', '2,3')
) as g(matrikel, modulname, grade_value)
join student s on s.matrikel = g.matrikel
join module m on m.name = g.modulname
on conflict do nothing;
```

### Error Handling in FastAPI
```python
from fastapi import HTTPException

if duplicate_found:
    raise HTTPException(
        status_code=409,
        detail="Resource already exists"
    )
```

### CSV Export
```python
import csv
import io

@app.get("/grades.csv")
async def export_csv():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT ... FROM grade JOIN ...")
        rows = cur.fetchall()

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["col1", "col2"])
    writer.writeheader()
    writer.writerows(rows)

    return Response(
        content=buf.getvalue().encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=export.csv"}
    )
```

---

## Zusammenfassung

Der **Grades-Starter** bietet eine solide Grundlage für FastAPI + PostgreSQL + MQTT Apps:

- ✅ Klare Projekt-Struktur
- ✅ Bewährte Patterns (dict_row, Pydantic, Context Manager)
- ✅ Docker-basierte Entwicklung
- ✅ Idempotente Datenbank-Initialisierung

Für die **Inventar-App** haben wir diese Patterns erfolgreich übernommen und um spezifische Domain-Regeln und erweiterte Validierung ergänzt.
