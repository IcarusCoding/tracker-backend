import uuid
from typing import Optional

from sqlmodel import Session

from crud import crud
from models import Role
from models.user import Scope


def create_scope(db: Session, scope_name: str) -> Scope:
    return crud.create(db, model=Scope, name=scope_name)


def delete_scope(db: Session, scope_id: uuid.UUID) -> None:
    crud.delete(db, model=Scope, obj_id=scope_id)


def get_scope(db: Session, scope_id: uuid.UUID) -> Optional[Scope]:
    return crud.get(db, model=Scope, obj_id=scope_id)


def get_scope_by_name(db: Session, scope_name: str) -> Optional[Scope]:
    return crud.get_by_name(db, model=Scope, name=scope_name)


def assign_scope_to_role(db: Session, role: Role, scope: Scope) -> None:
    if not scope in role.scopes:
        role.scopes.append(scope)
        crud.refresh(db, role)
