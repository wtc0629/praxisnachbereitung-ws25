from datetime import datetime
from pydantic import BaseModel
from typing import Optional


# Person Models
class Person(BaseModel):
    person_id: int
    personnel_no: str
    name: str
    email: Optional[str] = None
    created_at: datetime


class PersonCreate(BaseModel):
    personnel_no: str
    name: str
    email: Optional[str] = None


# DeviceType Models
class DeviceType(BaseModel):
    device_type_id: int
    code: str
    name: str
    description: Optional[str] = None


class DeviceTypeCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None


# Location Models
class Location(BaseModel):
    location_id: int
    code: str
    name: str
    address: Optional[str] = None


class LocationCreate(BaseModel):
    code: str
    name: str
    address: Optional[str] = None


# Device Models
class Device(BaseModel):
    device_id: int
    inventory_no: str
    device_type_id: int
    location_id: int
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DeviceCreate(BaseModel):
    inventory_no: str
    device_type_id: int
    location_id: int
    status: str = "in_stock"
    notes: Optional[str] = None


class DeviceUpdate(BaseModel):
    device_type_id: Optional[int] = None
    location_id: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


# Assignment Models
class Assignment(BaseModel):
    assignment_id: int
    device_id: int
    person_id: int
    assigned_from: datetime
    assigned_to: Optional[datetime] = None
    notes: Optional[str] = None
    damage_notes: Optional[str] = None


class AssignmentCreate(BaseModel):
    device_id: int
    person_id: int
    assigned_from: Optional[datetime] = None
    notes: Optional[str] = None


class AssignmentReturn(BaseModel):
    assigned_to: Optional[datetime] = None
    damage_notes: Optional[str] = None
