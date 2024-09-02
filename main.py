import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager

from database import init_database

from models import *

from routers import user, role, auth, scope, device

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger('passlib').setLevel(logging.ERROR)
    init_database()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(user.router)
app.include_router(role.router)
app.include_router(auth.router)
app.include_router(scope.router)
app.include_router(device.router)
