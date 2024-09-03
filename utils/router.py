from typing import Generic, Type

from fastapi import APIRouter, status, Depends, HTTPException
from sqlmodel import Session, SQLModel
from typing_extensions import TypeVar

from controller.auth import ScopeValidator
from deps import get_session
from utils.crud import GenericCRUD
from utils.models import ObjectIdentifier

Model = TypeVar("Model", bound=SQLModel)
Create = TypeVar("Create", bound=SQLModel)
Read = TypeVar("Read", bound=SQLModel)
CRUD = TypeVar("CRUD", bound=GenericCRUD)


class GenericRouter(APIRouter, Generic[Model, Create, Read, CRUD]):

    # TODO decorator
    def __init__(self, model: Type[Model],
                 read_model: Type[Read],
                 create_model: Type[Create],
                 crud_model: Type[CRUD],
                 tag: str,
                 # TODO proper generics
                 crud: CRUD = None,
                 prefix: str = ""):
        super().__init__(prefix=prefix, tags=[tag], dependencies=[])
        self.model = model
        self.read_model = read_model
        self.create_model = create_model
        self.crud_model = crud_model
        self.tag = tag
        if not crud:
            # TODO proper DI
            crud = crud_model(model=self.model, session=next(get_session()))
        self.crud = crud
        self.setup()
        self.extension()

    async def create_item(self, item: Create, crud: CRUD):
        return crud.create(**item.model_dump())

    async def get_item(self, obj_id: ObjectIdentifier, crud: CRUD):
        return crud.read(obj_id)

    async def get_all_items(self, skip: int, limit: int, crud: CRUD):
        return crud.read_all(skip=skip, limit=limit)

    async def delete_item(self, obj_id: ObjectIdentifier, crud: CRUD):
        crud.delete(obj_id)

    def extension(self):
        pass

    def setup(self):
        model = self.model
        read_model = self.read_model
        create_model = self.create_model
        tag = self.tag
        crud = self.crud

        @self.post("/", response_model=read_model, status_code=status.HTTP_201_CREATED,
                   description=f"Creates a new {model.__name__} using {read_model.__name__}",
                   name=f"Create a new {model.__name__}")
        async def create_route(create_obj: create_model, session: Session = Depends(get_session),
                               _: None = Depends(ScopeValidator(f"{tag}:create"))) -> Read:
            return await self.create_item(create_obj, session, crud)

        @self.get("/id/{obj_id}", response_model=read_model, status_code=status.HTTP_200_OK,
                  description=f"Retrieves an existing {model.__name__} by its id",
                  name=f"Retrieve a {model.__name__}")
        async def get_route(obj_id: ObjectIdentifier = Depends(),
                            _: None = Depends(ScopeValidator(f"{tag}:read"))):
            obj = await self.get_item(obj_id, crud)
            if not obj:
                raise HTTPException(status_code=404, detail=f"{obj_id} not found")
            return obj

        @self.get("/", response_model=list[read_model],
                  description=f"Retrieves all existing {model.__name__} entities",
                  name=f"Retrieve all {model.__name__} entities")
        async def get_all_route(_: None = Depends(ScopeValidator(f"{tag}:read")),
                                skip: int = 0, limit: int = 10):
            return await self.get_all_items(skip, limit, crud)

        @self.delete("/{obj_id}", status_code=status.HTTP_204_NO_CONTENT,
                     description=f"Deletes an existing {model.__name__}",
                     name=f"Delete a {model.__name__}")
        async def delete_route(obj_id: ObjectIdentifier = Depends(),
                               _: None = Depends(ScopeValidator(f"{tag}:delete"))):
            if not crud.read(obj_id):
                raise HTTPException(status_code=404, detail=f"{obj_id} not found")
            return await self.delete_item(obj_id, crud)
