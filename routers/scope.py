import uuid

from fastapi import APIRouter, status, Depends, HTTPException
from sqlmodel import Session

import crud
from controller import RoleValidator
from deps import get_session
from models.user import Scope, ScopeCreate, Role

router = APIRouter(prefix="/scopes", tags=["scopes"], dependencies=[Depends(RoleValidator(["admin"]))])


@router.post("/", response_model=Scope, status_code=status.HTTP_201_CREATED)
def create_scope(scope: ScopeCreate, db: Session = Depends(get_session)):
    if crud.scope.get_scope_by_name(db, scope.name):
        raise HTTPException(status_code=400, detail="Scope already exists")
    return crud.scope.create_scope(db, scope.name)


@router.delete("/id", status_code=status.HTTP_204_NO_CONTENT)
def delete_scope(scope_id: uuid.UUID, db: Session = Depends(get_session)):
    if not crud.scope.get_scope(db, scope_id):
        raise HTTPException(status_code=404, detail="Scope not found")
    crud.scope.delete_scope(db, scope_id)
    return None


@router.delete("/name", status_code=status.HTTP_204_NO_CONTENT)
def delete_scope(scope_name: str, db: Session = Depends(get_session)):
    scope = crud.get_scope_by_name(db, scope_name)
    if not scope:
        raise HTTPException(status_code=404, detail="Scope not found")
    crud.scope.delete_scope(db, scope.id)
    return None


@router.post("/{role_name}/scopes/{scope_name}", response_model=Role)
def assign_scope_to_role(role_name: str, scope_name: str, db: Session = Depends(get_session)):
    role = crud.role.get_role_by_name(db, role_name)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    scope = crud.scope.get_scope_by_name(db, scope_name)
    if not scope:
        raise HTTPException(status_code=404, detail="Scope not found")

    crud.scope.assign_scope_to_role(db, role, scope)
    return role
