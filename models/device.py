import secrets
import string
import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship

from models import User


def generate_random_apikey(length: int = 32) -> str:
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


class ApiKey(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created: datetime = Field(default_factory=datetime.now)
    apikey: str = Field(default_factory=lambda: generate_random_apikey(), unique=True)


class DeviceBase(SQLModel):
    name: str = Field(max_length=30, unique=True, index=True)
    description: str = Field(max_length=255)


class DeviceInfo(DeviceBase):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created: datetime = Field(default_factory=datetime.now)
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, foreign_key="user.id")


class Device(DeviceInfo, table=True):
    apikey_id: uuid.UUID = Field(default=None, foreign_key="apikey.id", unique=True, nullable=True, ondelete="CASCADE")
    user: User = Relationship(back_populates="devices")
    locations: list["Location"] = Relationship(back_populates="device", cascade_delete=True)


class DeviceCreateOther(DeviceBase):
    user_id: uuid.UUID


class DeviceCreate(DeviceBase):
    pass


class LocationBase(SQLModel):
    date: datetime = Field(default_factory=datetime.now)
    latitude: float = Field()
    longitude: float = Field()


class Location(LocationBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    device_id: uuid.UUID = Field(foreign_key="device.id")

    device: Device = Relationship(back_populates="locations")
