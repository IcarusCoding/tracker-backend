from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from controller import auth
from deps import get_session
from models import Token, UserLogin

router = APIRouter(tags=["auth"])


@router.post("/token", response_model=Token)
def login(user_login: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_session)):
    print("adssad")
    user = auth.auth_user(UserLogin(name=user_login.username, password=user_login.password), db)
    return auth.create_token(user)
