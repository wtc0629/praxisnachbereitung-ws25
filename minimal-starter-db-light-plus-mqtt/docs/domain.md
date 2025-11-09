# Inventar-Domänenmodell

## Entity-Relationship-Diagramm (Mermaid)
```mermaid
erDiagram
    Person ||--o{ Assignment : "hat"
    Device ||--o{ Assignment : "wird_zugewiesen"
    DeviceType ||--o{ Device : "kategorisiert"
    Location ||--o{ Device : "befindet_sich"
    
    Person {
        int person_id PK
        string personnel_no UK "Personalnummer"
        string name
        string email
        datetime created_at
    }
    
    DeviceType {
        int device_type_id PK
        string code UK "z.B. LAPTOP, MONITOR"
        string name
        string description
    }
    
    Location {
        int location_id PK
        string code UK "z.B. HQ, REMOTE, LAB"
        string name
        string address
    }
    
    Device {
        int device_id PK
        string inventory_no UK "Inventarnummer"
        int device_type_id FK
        int location_id FK
        string status "in_use, in_stock, repair, retired"
        datetime created_at
        datetime updated_at
    }
    
    Assignment {
        int assignment_id PK
        int device_id FK
        int person_id FK
        datetime assigned_from
        datetime assigned_to "NULL = aktiv"
        string notes
    }
```

## Geschäftsregeln

### R1: Eindeutigkeitsregeln (UK - Unique Keys)
- `Person.personnel_no` ist eindeutig (z.B. "P001", "P002")
- `DeviceType.code` ist eindeutig (z.B. "LAPTOP", "MONITOR")
- `Location.code` ist eindeutig (z.B. "HQ", "REMOTE")
- `Device.inventory_no` ist eindeutig (z.B. "INV-2025-001")

### R2: Aktive Zuweisung
- Zu einem Zeitpunkt darf ein Device höchstens **eine aktive Zuweisung** haben
- Aktive Zuweisung = `Assignment.assigned_to IS NULL`
- Implementierung: Unique-Constraint oder Check in der Anwendungslogik

### R3: Historisierung
- Vergangene Zuweisungen werden **nicht gelöscht**, sondern mit `assigned_to` 
  abgeschlossen
- Dadurch: vollständige Historie pro Device

### R4: Device-Status
- Erlaubte Werte für `Device.status`:
  - `in_use` - in Benutzung (hat aktive Zuweisung)
  - `in_stock` - auf Lager (keine aktive Zuweisung)
  - `repair` - in Reparatur
  - `retired` - ausgemustert

### R5: Zeitliche Konsistenz
- `assigned_from` < `assigned_to` (falls assigned_to nicht NULL)
- Keine überlappenden Assignments für dasselbe Device

## Normalisierung

- **1NF**: Alle Attribute sind atomar (keine Listen oder zusammengesetzten Werte)
- **2NF/3NF**: Stammdaten (Person, DeviceType, Location) getrennt von 
  Bewegungsdaten (Assignment)
- Vermeidung von Redundanz durch Fremdschlüssel-Beziehungen

