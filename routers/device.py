import uuid

from fastapi import Depends, status, HTTPException
from fastapi_utils.cbv import cbv

from controller.auth import ScopeValidator, get_user, ImplicitScopeValidator
from models import Device, DeviceCreate, DeviceInfo, ApiKey
from models import User
from utils.models import ObjectIdentifier
from utils.router import Models, UniqueNameRouter

device_models = Models(base=Device, read=DeviceInfo)

router = UniqueNameRouter(device_models, tag="devices", prefix="/devices")


@cbv(router)
class RouterExtension:
    user: User = Depends(get_user)
    validator: ImplicitScopeValidator = Depends(ImplicitScopeValidator("devices:others:apikey"))

    @router.post("/", response_model=DeviceInfo, status_code=status.HTTP_201_CREATED,
                 description=f"Creates a new Device for the authenticated User",
                 name=f"Create a new Device")
    def create_device(self, device_create: DeviceCreate = Depends(),
                      _: None = Depends(ScopeValidator("devices:create"))):
        router.validate_uniques(device_create, ObjectIdentifier(id=self.user.id))
        return router.crud.create(Device, owner_id=self.user.id, **device_create.model_dump())

    @router.post("/others", response_model=DeviceInfo, status_code=status.HTTP_201_CREATED,
                 description=f"Creates a new Device for the specified User",
                 name=f"Create a new Device for another User")
    def create_device_others(self, user_id: uuid.UUID, device_create: DeviceCreate = Depends(),
                             _: None = Depends(ScopeValidator("devices:others:create"))):
        if not router.crud.exists(User, id___is=user_id):
            raise HTTPException(status_code=404, detail=f"User with id '{user_id}' not found")
        router.validate_uniques(device_create, ObjectIdentifier(id=user_id))
        return router.crud.create(Device, owner_id=user_id, **device_create.model_dump())

    @router.post("/apikey", response_model=ApiKey, status_code=status.HTTP_201_CREATED,
                 description=f"Generates a new ApiKey for the given Device",
                 name=f"Generates a new ApiKey")
    def create_apikey(self, device_id: uuid.UUID,
                      _: None = Depends(ScopeValidator("devices:others:apikey"))):
        device: Device = router.crud.read_raw(Device, id___is=device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device with id {device_id} not found")
        if device.owner_id != self.user.id:
            self.validator.validate(self.user)
        router.crud.delete_raw(ApiKey, device_id___is=device_id)
        key: ApiKey = router.crud.create(ApiKey, device_id=device_id)
        router.crud.refresh(device)
        router.crud.refresh(key)
        return key
