import uuid

from sqlmodel import Session

import crud
from models import Device


def create_device(db: Session, device: Device):
    return crud.create(db, model=Device, **device.model_dump())


def get_device(db: Session, device_id: uuid.UUID):
    return crud.get(db, model=Device, obj_id=device_id)


def get_device_by_name(db: Session, device_name: str):
    return crud.get_by_name(db, model=Device, name=device_name)
