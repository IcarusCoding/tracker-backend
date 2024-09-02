import uuid

from fastapi import APIRouter, status, Depends, HTTPException
from sqlmodel import Session

import crud
from controller.auth import ScopeValidator
from deps import get_session
from models import UserRead, User, UserCreate, UserUpdate, Role, RoleCreate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user_create: UserCreate, _: None = Depends(ScopeValidator("users:create")),
                db: Session = Depends(get_session)):
    user = User(**user_create.model_dump())
    if crud.get_user_by_name(db, user.name):
        raise HTTPException(status_code=400, detail="Username already exists")
    return crud.user.create_user(db, user)


@router.get("/", response_model=list[UserRead])
def get_users(_: None = Depends(ScopeValidator("users:read")), skip: int = 0, limit: int = 10,
              db: Session = Depends(get_session)):
    return crud.user.get_users(db, skip, limit)


@router.patch("/{user_id}", response_model=UserRead)
def patch_user(user_id: uuid.UUID, user_update: UserUpdate, _: None = Depends(ScopeValidator("users:update")),
               db: Session = Depends(get_session)):
    user_before = crud.get_user_by_name(db, user_update.name)
    if user_before and user_id != user_before.id:
        raise HTTPException(status_code=400, detail="Username already exists")
    updated_user = crud.user.update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user


@router.put("/{user_id}", response_model=UserRead)
def update_user(user_id: uuid.UUID, user_update: UserUpdate, _: None = Depends(ScopeValidator("users:update")),
                db: Session = Depends(get_session)):
    if not (user_update.name and user_update.password):
        raise HTTPException(status_code=400, detail="Not all attributes were given")
    return patch_user(user_id, user_update, db)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: uuid.UUID, _: None = Depends(ScopeValidator("users:delete")),
                db: Session = Depends(get_session)):
    if not crud.user.get_user(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    crud.delete_user(db, user_id)
    return None


@router.get("/id/{user_id}", response_model=UserRead)
def get_user(user_id: uuid.UUID, _: None = Depends(ScopeValidator("users:read")),
             db: Session = Depends(get_session)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/name/{username}", response_model=UserRead)
def get_user_by_name(username: str, _: None = Depends(ScopeValidator("users:read")),
                     db: Session = Depends(get_session)):
    user = crud.get_user_by_name(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
