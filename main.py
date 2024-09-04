import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from init import init_database
from models import *
from routers import auth
from routers.device import DeviceRouter
from routers.role import RoleRouter
from routers.scope import ScopeRouter
from utils.router import UniqueNameRouter, Models


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger('passlib').setLevel(logging.ERROR)
    init_database(app)
    yield


app = FastAPI(lifespan=lifespan, swagger_ui_parameters={"operationsSorter": "method"})

user_models = Models(base=User, create=UserCreate, read=UserRead, update=UserUpdate)
app.include_router(UniqueNameRouter(user_models, tag="users", prefix="/users"))

app.include_router(DeviceRouter())
app.include_router(RoleRouter())
app.include_router(ScopeRouter())

app.include_router(auth.router)
