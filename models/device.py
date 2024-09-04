import secrets
import string
import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship

from models import User
from utils.models import NamedObject, ObjectIdentifier


def generate_random_apikey(length: int = 32) -> str:
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


class ApiKey(ObjectIdentifier, table=True):
    created: datetime = Field(default_factory=datetime.now)
    apikey: str = Field(default_factory=lambda: generate_random_apikey(), unique=True)
    device_id: Optional[uuid.UUID] = Field(default=None, foreign_key="device.id", ondelete="CASCADE", nullable=False)

    device: Optional["Device"] = Relationship(back_populates="apikey")


class DeviceBase(NamedObject):
    description: str = Field(max_length=255)


class DeviceInfo(DeviceBase):
    created: datetime = Field(default_factory=datetime.now)
    owner_id: uuid.UUID = Field(default_factory=uuid.uuid4, foreign_key="user.id")


class Device(DeviceInfo, table=True):
    user: User = Relationship(back_populates="devices")
    locations: list["Location"] = Relationship(back_populates="device", cascade_delete=True)

    apikey: Optional[ApiKey] = Relationship(back_populates="device",
                                            sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False})


class DeviceCreateOther(SQLModel):
    name: str
    description: str
    owner_id: uuid.UUID


class DeviceCreate(SQLModel):
    name: str
    description: str


class LocationBase(SQLModel):
    date: datetime = Field(default_factory=datetime.now)
    latitude: float = Field()
    longitude: float = Field()


class Location(ObjectIdentifier, table=True):
    device_id: uuid.UUID = Field(foreign_key="device.id")

    device: Device = Relationship(back_populates="locations")
