from dataclasses import dataclass
from typing import Generic, Type, Optional

from fastapi import APIRouter, status, Depends, HTTPException
from sqlmodel import SQLModel
from typing_extensions import TypeVar, override

from controller.auth import ScopeValidator
from deps import get_session
from utils.crud import GenericCRUD
from utils.models import ObjectIdentifier, NamedObject

Model = TypeVar("Model", bound=Optional[ObjectIdentifier])
Create = TypeVar("Create", bound=Optional[SQLModel])
Read = TypeVar("Read", bound=Optional[SQLModel])
Update = TypeVar("Update", bound=Optional[SQLModel])
Delete = TypeVar("Delete", bound=Optional[ObjectIdentifier])
CRUD = TypeVar("CRUD", bound=GenericCRUD)

NamedModel = TypeVar("NamedModel", bound=NamedObject)


@dataclass
class Models:
    base: Type[Model]
    create: Type[Create] = None
    read: Type[Read] = None
    update: Type[Update] = None
    delete: Type[Delete] = ObjectIdentifier
    crud: Type[CRUD] = GenericCRUD


class GenericRouter(APIRouter, Generic[Model, Create, Read, Update, Delete, CRUD]):

    def __init__(self, models: Models, tag: str, crud: CRUD = None, prefix: str = ""):
        super().__init__(prefix=prefix, tags=[tag])
        self.models = models
        self.tag = tag
        if not crud:
            crud = models.crud(session=next(get_session()))
        self.crud = crud
        self.unique_columns = [column.name for column in models.base.__table__.columns if column.unique]
        self.setup()
        self.extension()

    async def create_item(self, item: Create, crud: CRUD):
        return crud.create(self.models.base, **item.model_dump())

    async def get_item(self, obj_id: ObjectIdentifier, crud: CRUD):
        return crud.read(self.models.base, obj_id)

    async def get_all_items(self, skip: int, limit: int, crud: CRUD):
        return crud.read_all(self.models.base, skip=skip, limit=limit)

    async def update_item(self, obj_id: ObjectIdentifier, item: Update, crud: CRUD):
        return crud.update(self.models.base, obj_id, **item.model_dump())

    async def delete_item(self, obj_id: ObjectIdentifier, crud: CRUD):
        crud.delete(self.models.base, obj_id)

    def _validate_uniques(self, obj, obj_id: ObjectIdentifier = None):
        for column in self.unique_columns:
            if hasattr(obj, column):
                value = getattr(obj, column)
                model_obj = self.crud.read_raw(self.models.base, **{column: value})
                if model_obj and (not obj_id or model_obj.id != obj_id.id):
                    raise HTTPException(status_code=400, detail=f"Value '{column}={value}' is already in use")

    def extension(self):
        pass

    def setup(self):
        models = self.models
        tag = self.tag
        crud = self.crud

        if models.create:
            @self.post("/", response_model=models.read, status_code=status.HTTP_201_CREATED,
                       description=f"Creates a new {models.base.__name__} using {models.create.__name__}",
                       name=f"Create a new {models.base.__name__}")
            async def create_route(create_obj: models.create = Depends(),
                                   _: None = Depends(ScopeValidator(f"{tag}:create"))) -> Read:
                self._validate_uniques(create_obj)
                return await self.create_item(create_obj, crud)

        if models.read:
            @self.get("/id/{id}", response_model=models.read, status_code=status.HTTP_200_OK,
                      description=f"Retrieves an existing {models.base.__name__} by its id",
                      name=f"Retrieve a {models.base.__name__}")
            async def get_route(id: ObjectIdentifier = Depends(),
                                _: None = Depends(ScopeValidator(f"{tag}:read"))):
                obj = await self.get_item(id, crud)
                if not obj:
                    raise HTTPException(status_code=404, detail=f"'{id}' not found")
                return obj

        if models.read:
            @self.get("/", response_model=list[models.read],
                      description=f"Retrieves all existing {models.base.__name__} entities",
                      name=f"Retrieve all {models.base.__name__} entities")
            async def get_all_route(_: None = Depends(ScopeValidator(f"{tag}:read")),
                                    skip: int = 0, limit: int = 10):
                return await self.get_all_items(skip, limit, crud)

        if models.update:
            @self.patch("/{id}", response_model=models.read,
                        description=f"Patches an existing {models.base.__name__} by attributes",
                        name=f"Patch a {models.base.__name__}")
            async def patch_route(opt_type: models.update = Depends(), id: ObjectIdentifier = Depends(),
                                  _: None = Depends(ScopeValidator(f"{tag}:update"))):
                if not crud.exists(models.base, id___is=id.id):
                    raise HTTPException(status_code=404, detail=f"'{id}' not found")
                self._validate_uniques(opt_type, id)
                return await self.update_item(id, opt_type, crud)

            @self.put("/{id}", response_model=models.read,
                      description=f"Updates an existing {models.base.__name__}",
                      name=f"Update a {models.base.__name__}")
            async def update_route(update_obj: models.update = Depends(), id: ObjectIdentifier = Depends(),
                                   _: None = Depends(ScopeValidator(f"{tag}:update"))):
                if not all(update_obj.model_dump().values()):
                    raise HTTPException(status_code=400, detail="Not all attributes were given")
                return await patch_route(update_obj, id)

        if models.delete:
            @self.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT,
                         description=f"Deletes an existing {models.base.__name__}",
                         name=f"Delete a {models.base.__name__}")
            async def delete_route(id: models.delete = Depends(),
                                   _: None = Depends(ScopeValidator(f"{tag}:delete"))):
                if not crud.read(self.models.base, id):
                    raise HTTPException(status_code=404, detail=f"'{id}' not found")
                return await self.delete_item(id, crud)


class UniqueNameRouter(GenericRouter[NamedModel, Create, Read, Update, Delete, GenericCRUD]):
    def __init__(self, models: Models, tag: str, crud: CRUD = None,
                 prefix: str = ""):
        super().__init__(models, tag, crud, prefix)
        if not issubclass(models.base, NamedObject):
            raise ValueError("Only named objects are supported")

    @override
    def setup(self):
        super().setup()
        router = self

        if self.models.read:
            @router.get("/name/{name}", response_model=router.models.read,
                        description=f"Retrieves an existing {router.models.base.__name__} by its name",
                        name=f"Retrieve a {router.models.base.__name__}")
            async def get_by_name_route(name: str, _: None = Depends(ScopeValidator(f"{router.tag}:read"))):
                obj = router.crud.read_raw(self.models.base, name___is=name)
                if not obj:
                    raise HTTPException(status_code=404, detail=f"{name} not found")
                return obj

        if self.models.delete:
            @router.delete("/name/{name}", status_code=status.HTTP_204_NO_CONTENT,
                           description=f"Deletes an existing {router.models.base.__name__} by its name",
                           name=f"Delete a {router.models.base.__name__}")
            async def delete_by_name_route(name: str, _: None = Depends(ScopeValidator(f"{router.tag}:delete"))):
                obj = router.crud.read_raw(self.models.base, name___is=name)
                if not obj:
                    raise HTTPException(status_code=404, detail=f"{name} not found")
                router.crud.delete(self.models.base, ObjectIdentifier(id=obj.id))
