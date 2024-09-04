import os

from fastapi import FastAPI
from sqlmodel import SQLModel, Session

from controller.auth import ScopeValidator
from database import engine
from models import User, Role
from models.user import Scope
from utils.crud import GenericCRUD


def init_database(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        crud = GenericCRUD(session=session)

        # Admin user
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv("ADMIN_PASSWORD", "admin")
        admin_user = crud.read_raw(User, name___is=username)
        if not admin_user:
            admin_user = crud.create(User, **{"name": username, "password": password})

        # Admin role
        admin_role = crud.read_raw(Role, name___is="admin")
        if not admin_role:
            admin_role = crud.create(Role, **{"name": "admin"})

        # Scopes
        for scope_name in ScopeValidator.registered_scopes:
            scope = crud.read_raw(Scope, name___is=scope_name)
            if not scope:
                scope = crud.create(Scope, **{"name": scope_name})
            # Assign scopes to admin role
            if scope not in admin_role.scopes:
                admin_role.scopes.append(scope)
            crud.refresh(admin_role)

        # Assign admin role to admin user
        if admin_role not in admin_user.roles:
            admin_user.roles.append(admin_role)
            crud.refresh(admin_user)
