from dataclasses import dataclass
from typing import Generic, Type, Optional

from fastapi import APIRouter, status, Depends, HTTPException
from sqlmodel import SQLModel
from typing_extensions import TypeVar, override

from controller.auth import ScopeValidator
from deps import get_session
from utils.crud import GenericCRUD, UniqueNameCRUD
from utils.models import ObjectIdentifier

Model = TypeVar("Model", bound=Optional[SQLModel])
Create = TypeVar("Create", bound=Optional[SQLModel])
Read = TypeVar("Read", bound=Optional[SQLModel])
Update = TypeVar("Update", bound=Optional[SQLModel])
Delete = TypeVar("Delete", bound=Optional[ObjectIdentifier])
CRUD = TypeVar("CRUD", bound=GenericCRUD)

UCRUD = TypeVar("UCRUD", bound=UniqueNameCRUD)


@dataclass
class Models:
    base: Type[Model]
    create: Type[Create] = None
    read: Type[Read] = None
    update: Type[Update] = None
    delete: Type[Delete] = ObjectIdentifier
    crud: Type[CRUD] = GenericCRUD


class GenericRouter(APIRouter, Generic[Model, Create, Read, Update, Delete, CRUD]):

    # TODO decorator
    def __init__(self, models: Models, tag: str, crud: CRUD = None, prefix: str = ""):
        super().__init__(prefix=prefix, tags=[tag], dependencies=[])
        self.models = models
        self.tag = tag
        if not crud:
            # TODO proper DI
            crud = models.crud(model=models.base, session=next(get_session()))
        self.crud = crud
        self.setup()
        self.extension()

    async def create_item(self, item: Create, crud: CRUD):
        return crud.create(**item.model_dump())

    async def get_item(self, obj_id: ObjectIdentifier, crud: CRUD):
        return crud.read(obj_id)

    async def get_all_items(self, skip: int, limit: int, crud: CRUD):
        return crud.read_all(skip=skip, limit=limit)

    async def update_item(self, obj_id: ObjectIdentifier, item: Update, crud: CRUD):
        return crud.update(obj_id, **item.model_dump())

    async def delete_item(self, obj_id: ObjectIdentifier, crud: CRUD):
        crud.delete(obj_id)

    def extension(self):
        pass

    def setup(self):
        models = self.models
        tag = self.tag
        crud = self.crud

        if models.create:
            @self.post("/", response_model=models.read, status_code=status.HTTP_201_CREATED,
                       description=f"Creates a new {models.base.__name__} using {models.read.__name__}",
                       name=f"Create a new {models.base.__name__}")
            async def create_route(create_obj: models.create = Depends(),
                                   _: None = Depends(ScopeValidator(f"{tag}:create"))) -> Read:
                return await self.create_item(create_obj, crud)

        if models.read:
            @self.get("/id/{id}", response_model=models.read, status_code=status.HTTP_200_OK,
                      description=f"Retrieves an existing {models.base.__name__} by its id",
                      name=f"Retrieve a {models.base.__name__}")
            async def get_route(id: ObjectIdentifier = Depends(),
                                _: None = Depends(ScopeValidator(f"{tag}:read"))):
                obj = await self.get_item(id, crud)
                if not obj:
                    raise HTTPException(status_code=404, detail=f"{id} not found")
                return obj

        if models.read:
            @self.get("/", response_model=list[models.read],
                      description=f"Retrieves all existing {models.base.__name__} entities",
                      name=f"Retrieve all {models.base.__name__} entities")
            async def get_all_route(_: None = Depends(ScopeValidator(f"{tag}:read")),
                                    skip: int = 0, limit: int = 10):
                return await self.get_all_items(skip, limit, crud)

        if models.update:
            @self.put("/{id}", response_model=models.read,
                      description=f"Updates an existing {models.base.__name__}",
                      name=f"Update a {models.base.__name__}")
            async def update_route(update_obj: models.update = Depends(), id: ObjectIdentifier = Depends(),
                                   _: None = Depends(ScopeValidator(f"{tag}:update"))):
                if not all(models.update.values()):
                    raise HTTPException(status_code=400, detail="Not all attributes were given")
                return await self.update_item(id, update_obj, crud)

        if models.delete:
            @self.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT,
                         description=f"Deletes an existing {models.base.__name__}",
                         name=f"Delete a {models.base.__name__}")
            async def delete_route(id: models.delete = Depends(),
                                   _: None = Depends(ScopeValidator(f"{tag}:delete"))):
                if not crud.read(id):
                    raise HTTPException(status_code=404, detail=f"{id} not found")
                return await self.delete_item(id, crud)


class UniqueNameRouter(GenericRouter[Model, Create, Read, Update, Delete, UCRUD]):
    def __init__(self, models: Models, tag: str, crud: UCRUD = None,
                 prefix: str = ""):
        super().__init__(models, tag, crud, prefix)

    @override
    async def create_item(self, item: Create, crud: UCRUD):
        # TODO only allow models with a name
        if crud.read_by_name(item.name):
            raise HTTPException(status_code=400, detail="Name already exists")
        return await super().create_item(item, crud)

    @override
    def setup(self):
        super().setup()
        router = self

        @router.get("/name/{name}", response_model=router.models.read,
                    description=f"Retrieves an existing {router.models.base.__name__} by its name",
                    name=f"Retrieve a {router.models.base.__name__}")
        async def get_by_name_route(name: str, _: None = Depends(ScopeValidator(f"{router.tag}:read"))):
            obj = router.crud.read_by_name(name)
            if not obj:
                raise HTTPException(status_code=404, detail=f"{name} not found")
            return obj

        @router.delete("/name/{name}", status_code=status.HTTP_204_NO_CONTENT,
                       description=f"Deletes an existing {router.models.base.__name__} by its name",
                       name=f"Delete a {router.models.base.__name__}")
        async def delete_by_name_route(name: str, _: None = Depends(ScopeValidator(f"{router.tag}:read"))):
            obj = router.crud.read_by_name(name)
            if not obj:
                raise HTTPException(status_code=404, detail=f"{name} not found")
            router.crud.delete(ObjectIdentifier(id=obj.id))
