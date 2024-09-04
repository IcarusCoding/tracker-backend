import uuid
from typing import override

from fastapi import Depends, status, HTTPException

from controller.auth import ScopeValidator, get_user
from models import Device, DeviceCreate, DeviceInfo
from models import User
from utils.models import ObjectIdentifier
from utils.router import Models, UniqueNameRouter

device_models = Models(base=Device, read=DeviceInfo)


class DeviceRouter(UniqueNameRouter):

    def __init__(self):
        super().__init__(device_models, tag="devices", prefix="/devices")

    @override
    def extension(self):
        router = self

        @router.post("/", response_model=DeviceInfo, status_code=status.HTTP_201_CREATED,
                     description=f"Creates a new Device for the authenticated User",
                     name=f"Create a new Device")
        def create_device(device_create: DeviceCreate = Depends(), user: User = Depends(get_user),
                          _: None = Depends(ScopeValidator("devices:create"))):
            self._validate_uniques(device_create, ObjectIdentifier(id=user.id))
            return router.crud.create(Device, owner_id=user.id, **device_create.model_dump())

        @router.post("/others", response_model=DeviceInfo, status_code=status.HTTP_201_CREATED,
                     description=f"Creates a new Device for the specified User",
                     name=f"Create a new Device for another User")
        def create_device_others(user_id: uuid.UUID, device_create: DeviceCreate = Depends(),
                                 _: None = Depends(ScopeValidator("devices:others:create"))):
            if not router.crud.exists(User, id___is=user_id):
                raise HTTPException(status_code=404, detail=f"User with id '{user_id}' not found")
            self._validate_uniques(device_create, ObjectIdentifier(id=user_id))
            return router.crud.create(Device, owner_id=user_id, **device_create.model_dump())
