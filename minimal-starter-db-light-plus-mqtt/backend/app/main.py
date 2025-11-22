import csv
import io
import os
import json
from datetime import datetime

import paho.mqtt.client as mqtt
from fastapi import FastAPI, Request, Response, Query, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from .db import get_conn
from .models import (
    DeviceCreate, DeviceUpdate, AssignmentCreate, AssignmentReturn,
    PersonCreate, DeviceTypeCreate, LocationCreate
)

app = FastAPI(title="Inventar-App", version="0.3.0")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

MQTT_HOST = os.getenv("MQTT_HOST", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))


def mqtt_client() -> mqtt.Client:
    c = mqtt.Client()
    c.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
    return c


def publish_mqtt_event(topic: str, payload: dict):
    """Publiziert ein Event über MQTT"""
    try:
        c = mqtt_client()
        c.publish(topic, json.dumps(payload), qos=0, retain=False)
        c.disconnect()
    except Exception:
        pass  # MQTT-Fehler sollten die Hauptfunktion nicht blockieren


@app.get("/health")
async def health():
    db_state = "ok"
    mqtt_state = "ok"
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("select 1")
            cur.fetchone()
    except Exception as ex:
        db_state = f"error:{type(ex).__name__}"

    try:
        c = mqtt_client()
        c.disconnect()
    except Exception as ex:
        mqtt_state = f"degraded:{type(ex).__name__}"

    return {"status": "ok" if db_state == "ok" else "degraded", "db": db_state, "mqtt": mqtt_state}


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "DB-Light + MQTT Starter"})


@app.get("/inventory", response_class=HTMLResponse)
async def inventory_page(request: Request):
    return templates.TemplateResponse("inventory.html", {"request": request, "title": "Inventar-Verwaltung"})


@app.get("/reports/device-status")
async def device_status():
    sql = """
          select status, count(*) as cnt
          from device
          group by status
          order by status; \
          """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
    return rows


@app.get("/reports/device-status.csv")
async def device_status_csv():
    sql = """
          select status, count(*) as cnt
          from device
          group by status
          order by status; \
          """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["status", "cnt"], delimiter=";", lineterminator="\n")
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

    data = buf.getvalue().encode("utf-8-sig")
    headers = {"Content-Disposition": 'attachment; filename="device-status.csv"'}
    return Response(content=data, media_type="text/csv; charset=utf-8", headers=headers)


@app.post("/mqtt/publish")
async def mqtt_publish(topic: str = Query(...), payload: str = Query(...)):
    c = mqtt_client()
    c.publish(topic, payload, qos=0, retain=False)
    c.disconnect()
    return {"ok": True, "topic": topic, "payload": payload}


# ==========================================
# INVENTORY API ENDPOINTS
# ==========================================

# --- Devices Endpoints ---

@app.get("/devices")
async def get_devices():
    """Liste aller Geräte inkl. Typ, Standort, Status"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            select d.device_id, d.inventory_no, d.serial_number, d.status, d.notes,
                   d.created_at, d.updated_at,
                   dt.code as device_type_code, dt.name as device_type_name,
                   l.code as location_code, l.name as location_name,
                   case
                     when exists (
                       select 1 from assignment a
                       where a.device_id = d.device_id
                       and a.assigned_to is null
                     ) then 'ausgeliehen'
                     else 'frei'
                   end as availability_status
            from device d
            join device_type dt on dt.device_type_id = d.device_type_id
            join location l on l.location_id = d.location_id
            order by d.inventory_no
        """)
        devices = cur.fetchall()
    return devices


@app.post("/devices", status_code=201)
async def create_device(device: DeviceCreate):
    """
    Neues Gerät anlegen.
    Domain Rule IR-01: Eindeutige Seriennummer (serial_number)
    """
    with get_conn() as conn, conn.cursor() as cur:
        # Prüfen ob serial_number bereits existiert (IR-01)
        cur.execute("select device_id from device where serial_number = %s", (device.serial_number,))
        existing = cur.fetchone()

        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Device with serial_number '{device.serial_number}' already exists (IR-01 violated)"
            )

        # Device anlegen
        cur.execute("""
            insert into device (inventory_no, serial_number, device_type_id, location_id, status, notes)
            values (%s, %s, %s, %s, %s, %s)
            returning device_id, inventory_no, serial_number, device_type_id, location_id, status, notes, created_at, updated_at
        """, (device.inventory_no, device.serial_number, device.device_type_id, device.location_id, device.status, device.notes))

        new_device = cur.fetchone()

    return new_device


@app.get("/devices/{device_id}")
async def get_device(device_id: int):
    """Einzelnes Gerät abrufen"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            select d.device_id, d.inventory_no, d.serial_number, d.status, d.notes,
                   d.created_at, d.updated_at,
                   dt.device_type_id, dt.code as device_type_code, dt.name as device_type_name,
                   l.location_id, l.code as location_code, l.name as location_name
            from device d
            join device_type dt on dt.device_type_id = d.device_type_id
            join location l on l.location_id = d.location_id
            where d.device_id = %s
        """, (device_id,))
        device = cur.fetchone()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return device


@app.put("/devices/{device_id}")
async def update_device(device_id: int, device: DeviceUpdate):
    """Gerät aktualisieren"""
    with get_conn() as conn, conn.cursor() as cur:
        # Build update query dynamically
        updates = []
        params = []

        if device.device_type_id is not None:
            updates.append("device_type_id = %s")
            params.append(device.device_type_id)
        if device.location_id is not None:
            updates.append("location_id = %s")
            params.append(device.location_id)
        if device.status is not None:
            updates.append("status = %s")
            params.append(device.status)
        if device.notes is not None:
            updates.append("notes = %s")
            params.append(device.notes)

        updates.append("updated_at = now()")

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        params.append(device_id)
        query = f"update device set {', '.join(updates)} where device_id = %s returning *"

        cur.execute(query, params)
        updated_device = cur.fetchone()

        if not updated_device:
            raise HTTPException(status_code=404, detail="Device not found")

    return updated_device


@app.delete("/devices/{device_id}", status_code=204)
async def delete_device(device_id: int):
    """Gerät löschen"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("delete from device where device_id = %s returning device_id", (device_id,))
        deleted = cur.fetchone()

        if not deleted:
            raise HTTPException(status_code=404, detail="Device not found")


# --- Assignments Endpoints ---

@app.get("/assignments/active")
async def get_active_assignments():
    """Liste aller laufenden Ausleihen (assigned_to IS NULL)"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            select a.assignment_id, a.device_id, a.person_id,
                   a.assigned_from, a.assigned_to, a.notes,
                   d.inventory_no, d.status as device_status,
                   dt.name as device_type_name,
                   p.name as person_name, p.personnel_no
            from assignment a
            join device d on d.device_id = a.device_id
            join device_type dt on dt.device_type_id = d.device_type_id
            join person p on p.person_id = a.person_id
            where a.assigned_to is null
            order by a.assigned_from desc
        """)
        assignments = cur.fetchall()
    return assignments


@app.get("/assignments")
async def get_all_assignments():
    """Liste aller Ausleihen (auch zurückgegebene)"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            select a.assignment_id, a.device_id, a.person_id,
                   a.assigned_from, a.assigned_to, a.notes,
                   d.inventory_no, d.status as device_status,
                   dt.name as device_type_name,
                   p.name as person_name, p.personnel_no
            from assignment a
            join device d on d.device_id = a.device_id
            join device_type dt on dt.device_type_id = d.device_type_id
            join person p on p.person_id = a.person_id
            order by a.assigned_from desc
        """)
        assignments = cur.fetchall()
    return assignments


@app.post("/assignments", status_code=201)
async def create_assignment(assignment: AssignmentCreate):
    """
    Gerät ausgeben.
    Domain Rule IR-02: Max. eine aktive Ausleihe pro Gerät
    """
    with get_conn() as conn, conn.cursor() as cur:
        # Prüfen ob es bereits eine aktive Ausleihe für dieses Gerät gibt
        cur.execute("""
            select assignment_id from assignment
            where device_id = %s and assigned_to is null
        """, (assignment.device_id,))
        existing = cur.fetchone()

        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Device {assignment.device_id} already has an active assignment"
            )

        # Assignment anlegen
        assigned_from = assignment.assigned_from or datetime.now()

        cur.execute("""
            insert into assignment (device_id, person_id, assigned_from, notes)
            values (%s, %s, %s, %s)
            returning assignment_id, device_id, person_id, assigned_from, assigned_to, notes
        """, (assignment.device_id, assignment.person_id, assigned_from, assignment.notes))

        new_assignment = cur.fetchone()

        # MQTT Event publizieren
        publish_mqtt_event("inventory/assignments/issued", {
            "assignment_id": new_assignment["assignment_id"],
            "device_id": assignment.device_id,
            "person_id": assignment.person_id,
            "assigned_from": assigned_from.isoformat() if isinstance(assigned_from, datetime) else str(assigned_from)
        })

    return new_assignment


@app.post("/assignments/{assignment_id}/return")
async def return_assignment(assignment_id: int, return_data: AssignmentReturn):
    """
    Rückgabe eines Geräts.
    Domain Rule IR-03: Zeitlogik - assigned_to >= assigned_from
    """
    with get_conn() as conn, conn.cursor() as cur:
        # Assignment abrufen
        cur.execute("""
            select assignment_id, device_id, person_id, assigned_from, assigned_to
            from assignment where assignment_id = %s
        """, (assignment_id,))
        assignment = cur.fetchone()

        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        if assignment["assigned_to"] is not None:
            raise HTTPException(status_code=400, detail="Assignment already returned")

        # Zeitpunkt der Rückgabe
        assigned_to = return_data.assigned_to or datetime.now()

        # Zeitlogik prüfen: assigned_to >= assigned_from
        if assigned_to < assignment["assigned_from"]:
            raise HTTPException(
                status_code=422,
                detail=f"Return time ({assigned_to}) must be >= issue time ({assignment['assigned_from']})"
            )

        # Rückgabe setzen
        cur.execute("""
            update assignment
            set assigned_to = %s
            where assignment_id = %s
            returning assignment_id, device_id, person_id, assigned_from, assigned_to, notes
        """, (assigned_to, assignment_id))

        updated_assignment = cur.fetchone()

        # MQTT Event publizieren
        publish_mqtt_event("inventory/assignments/returned", {
            "assignment_id": assignment_id,
            "device_id": assignment["device_id"],
            "person_id": assignment["person_id"],
            "assigned_to": assigned_to.isoformat() if isinstance(assigned_to, datetime) else str(assigned_to)
        })

    return updated_assignment


# --- Helper Endpoints (Persons, DeviceTypes, Locations) ---

@app.get("/persons")
async def get_persons():
    """Liste aller Personen"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select * from person order by name")
        persons = cur.fetchall()
    return persons


@app.post("/persons", status_code=201)
async def create_person(person: PersonCreate):
    """Neue Person anlegen"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            insert into person (personnel_no, name, email)
            values (%s, %s, %s)
            on conflict (personnel_no) do nothing
            returning *
        """, (person.personnel_no, person.name, person.email))
        new_person = cur.fetchone()

        if not new_person:
            raise HTTPException(
                status_code=409,
                detail=f"Person with personnel_no '{person.personnel_no}' already exists"
            )

    return new_person


@app.get("/device-types")
async def get_device_types():
    """Liste aller Gerätetypen"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select * from device_type order by name")
        device_types = cur.fetchall()
    return device_types


@app.post("/device-types", status_code=201)
async def create_device_type(device_type: DeviceTypeCreate):
    """Neuen Gerätetyp anlegen"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            insert into device_type (code, name, description)
            values (%s, %s, %s)
            on conflict (code) do nothing
            returning *
        """, (device_type.code, device_type.name, device_type.description))
        new_device_type = cur.fetchone()

        if not new_device_type:
            raise HTTPException(
                status_code=409,
                detail=f"DeviceType with code '{device_type.code}' already exists"
            )

    return new_device_type


@app.get("/locations")
async def get_locations():
    """Liste aller Standorte"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select * from location order by name")
        locations = cur.fetchall()
    return locations


@app.post("/locations", status_code=201)
async def create_location(location: LocationCreate):
    """Neuen Standort anlegen"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            insert into location (code, name, address)
            values (%s, %s, %s)
            on conflict (code) do nothing
            returning *
        """, (location.code, location.name, location.address))
        new_location = cur.fetchone()

        if not new_location:
            raise HTTPException(
                status_code=409,
                detail=f"Location with code '{location.code}' already exists"
            )

    return new_location
