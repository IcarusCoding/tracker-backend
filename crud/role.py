import uuid
from typing import Optional

from sqlmodel import Session

import crud
from models import Role, User


def create_role(db: Session, role_name: str) -> Role:
    return crud.create(db, model=Role, name=role_name)


def delete_role(db: Session, role_id: uuid.UUID) -> None:
    crud.delete(db, model=Role, obj_id=role_id)


def get_role(db: Session, role_id: uuid.UUID) -> Optional[Role]:
    return crud.get(db, model=Role, obj_id=role_id)


def get_role_by_name(db: Session, role_name: str) -> Optional[Role]:
    return crud.get_by_name(db, model=Role, name=role_name)


def assign_role_to_user(db: Session, user: User, role: Role) -> None:
    if not role in user.roles:
        user.roles.append(role)
        crud.refresh(db, user)
