from fastapi import APIRouter, status, Depends, HTTPException
from sqlmodel import Session

import crud
from controller import get_user
from controller.auth import ScopeValidator
from deps import get_session
from models import DeviceInfo, Device, DeviceCreateOther, DeviceCreate, User

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("/create/others", response_model=DeviceInfo, status_code=status.HTTP_201_CREATED)
def create_device_others(device_create: DeviceCreateOther, _: None = Depends(ScopeValidator("devices:others:create")),
                         db: Session = Depends(get_session)):
    device = Device(**device_create.model_dump())
    if crud.device.get_device_by_name(db, device.name):
        raise HTTPException(status_code=400, detail=f"Device with name '{device.name}' already exists")
    if not crud.user.get_user(db, device.user_id):
        raise HTTPException(status_code=404, detail=f"User not found")
    return crud.device.create_device(db, device)


@router.post("/create", response_model=DeviceInfo, status_code=status.HTTP_201_CREATED)
def create_device(device_create: DeviceCreate, _: None = Depends(ScopeValidator("devices:create")),
                  db: Session = Depends(get_session), user: User = Depends(get_user)):
    device = Device(user_id=user.id, **device_create.model_dump())
    if crud.device.get_device_by_name(db, device.name):
        raise HTTPException(status_code=400, detail=f"Device with name '{device.name}' already exists")
    return crud.device.create_device(db, device)
