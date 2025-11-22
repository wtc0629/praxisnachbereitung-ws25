-- 010_inventory_schema.sql
-- Inventar-Schema für Department, Person, DeviceType, Location, Device, Assignment

-- DeviceType: Kategorisierung der Geräte
create table if not exists device_type (
  device_type_id serial primary key,
  code text not null unique,
  name text not null,
  description text
);

-- Location: Standorte
create table if not exists location (
  location_id serial primary key,
  code text not null unique,
  name text not null,
  address text
);

-- Person: Mitarbeiter/Personen
create table if not exists person (
  person_id serial primary key,
  personnel_no text not null unique,
  name text not null,
  email text,
  created_at timestamp not null default now()
);

-- Device: Geräte mit Inventarnummer
create table if not exists device (
  device_id serial primary key,
  inventory_no text not null unique,
  serial_number text not null unique,  -- IR-01: Eindeutige Seriennummer
  device_type_id int not null references device_type(device_type_id) on delete restrict,
  location_id int not null references location(location_id) on delete restrict,
  status text not null check (status in ('in_use','in_stock','repair','retired')) default 'in_stock',
  notes text,
  created_at timestamp not null default now(),
  updated_at timestamp not null default now()
);

-- Assignment: Zuweisung von Geräten an Personen
create table if not exists assignment (
  assignment_id serial primary key,
  device_id int not null references device(device_id) on delete restrict,
  person_id int not null references person(person_id) on delete restrict,
  assigned_from timestamp not null default now(),
  assigned_to timestamp,
  notes text,
  check (assigned_to is null or assigned_to >= assigned_from)
);

-- Index für Performance: häufige Abfrage aktiver Zuweisungen
create index if not exists idx_assignment_active on assignment(device_id) where assigned_to is null;

-- Seed-Daten für DeviceType
insert into device_type (code, name, description) values
  ('LAPTOP', 'Laptop', 'Tragbarer Computer'),
  ('MONITOR', 'Monitor', 'Bildschirm'),
  ('SCANNER', 'Handscanner', 'Mobiler Barcode-Scanner'),
  ('PRINTER', 'Drucker', 'Drucker'),
  ('TABLET', 'Tablet', 'Tablet-Computer')
on conflict (code) do nothing;

-- Seed-Daten für Location
insert into location (code, name, address) values
  ('HQ', 'Headquarters', 'Hauptstraße 1, 12345 Berlin'),
  ('REMOTE', 'Remote/Homeoffice', 'Verschiedene Standorte'),
  ('LAB', 'Labor', 'Technikraum, Gebäude B'),
  ('WAREHOUSE', 'Lager', 'Lagergebäude C')
on conflict (code) do nothing;

-- Seed-Daten für Person
insert into person (personnel_no, name, email) values
  ('P001', 'Alice Müller', 'alice.mueller@example.com'),
  ('P002', 'Bob Schmidt', 'bob.schmidt@example.com'),
  ('P003', 'Charlie Weber', 'charlie.weber@example.com'),
  ('P004', 'Diana Fischer', 'diana.fischer@example.com')
on conflict (personnel_no) do nothing;

-- Seed-Daten für Device
insert into device (inventory_no, serial_number, device_type_id, location_id, status, notes)
select d.inventory_no, d.serial_number, dt.device_type_id, l.location_id, d.status, d.notes
from (values
  ('INV-2025-001', 'SN-DELL-LAT-5520-001', 'LAPTOP', 'HQ', 'in_stock', 'Dell Latitude 5520'),
  ('INV-2025-002', 'SN-LENO-X1-2023-042', 'LAPTOP', 'REMOTE', 'in_use', 'Lenovo ThinkPad X1'),
  ('INV-2025-003', 'SN-DELL-MON-27-4K-003', 'MONITOR', 'HQ', 'in_stock', 'Dell 27" 4K'),
  ('INV-2025-004', 'SN-SAMS-24-2024-004', 'MONITOR', 'LAB', 'in_use', 'Samsung 24"'),
  ('INV-2025-005', 'SN-ZEBR-TC21-005', 'SCANNER', 'WAREHOUSE', 'in_stock', 'Zebra TC21'),
  ('INV-2025-006', 'SN-ZEBR-TC21-006', 'SCANNER', 'WAREHOUSE', 'repair', 'Zebra TC21 - defekt'),
  ('INV-2025-007', 'SN-APPL-IPAD-AIR-007', 'TABLET', 'REMOTE', 'in_use', 'iPad Air'),
  ('INV-2025-008', 'SN-HP-LJ-1998-008', 'PRINTER', 'HQ', 'retired', 'HP LaserJet - alt')
) as d(inventory_no, serial_number, device_type_code, location_code, status, notes)
join device_type dt on dt.code = d.device_type_code
join location l on l.code = d.location_code
on conflict (inventory_no) do nothing;

-- Seed-Daten für Assignment (einige aktive Zuweisungen)
insert into assignment (device_id, person_id, assigned_from, assigned_to, notes)
select dev.device_id, p.person_id, a.assigned_from, a.assigned_to::timestamp, a.notes
from (values
  ('INV-2025-002', 'P001', '2025-01-10 09:00:00'::timestamp, null, 'Homeoffice-Ausstattung'),
  ('INV-2025-004', 'P002', '2025-01-15 10:30:00'::timestamp, null, 'Labor-Arbeitsplatz'),
  ('INV-2025-007', 'P003', '2025-01-20 14:00:00'::timestamp, null, 'Außendienst')
) as a(inventory_no, personnel_no, assigned_from, assigned_to, notes)
join device dev on dev.inventory_no = a.inventory_no
join person p on p.personnel_no = a.personnel_no
on conflict do nothing;
