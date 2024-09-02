import uuid

from fastapi import APIRouter, status, Depends, HTTPException
from sqlmodel import Session

import crud
from controller import RoleValidator
from deps import get_session
from models import Role, RoleCreate, UserRead

router = APIRouter(prefix="/roles", tags=["roles"], dependencies=[Depends(RoleValidator(["admin"]))])


@router.post("/", response_model=Role, status_code=status.HTTP_201_CREATED)
def create_role(role: RoleCreate, db: Session = Depends(get_session)):
    if crud.role.get_role_by_name(db, role.name):
        raise HTTPException(status_code=400, detail="Role already exists")
    return crud.role.create_role(db, role.name)


@router.delete("/id", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: uuid.UUID, db: Session = Depends(get_session)):
    if not crud.get_role(db, role_id):
        raise HTTPException(status_code=404, detail="Role not found")
    crud.delete_role(db, role_id)
    return None


@router.delete("/name", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_name: str, db: Session = Depends(get_session)):
    role = crud.get_role_by_name(db, role_name)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    crud.delete_role(db, role.id)
    return None


@router.post("/{user_id}/roles/{role_name}", response_model=UserRead)
def assign_role_to_user(user_id: uuid.UUID, role_name: str, db: Session = Depends(get_session)):
    user = crud.user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = crud.role.get_role_by_name(db, role_name)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    crud.role.assign_role_to_user(db, user, role)
    return user
