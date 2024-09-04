import os
import uuid
from datetime import timedelta, datetime, timezone
from functools import wraps
from typing import Annotated, Optional

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlmodel import Session

from deps import get_session
from models import UserLogin, User, Token
from utils.crud import GenericCRUD
from utils.models import ObjectIdentifier

SIGN_ALGORITHM = "HS256"
SIGN_KEY = os.getenv("SIGN_KEY")
if SIGN_KEY is None:
    raise Exception("Missing SIGN_KEY environment variable")

ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 5)
REFRESH_TOKEN_EXPIRE_MINUTES = os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", 10)

oauth_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def auth_user(user_login: UserLogin, db: Session) -> User:
    crud = GenericCRUD(db)
    user: Optional[User] = crud.read_raw(User, name___is=user_login.name)

    if user and pwd_context.verify(user_login.password, user.password):
        return user

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user


def create_token(user: User) -> Token:
    access_token_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_delta = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

    data = {
        "iss": "gps-iam",
        "sub": str(user.id),
        "name": user.name,
        "roles": [role.name for role in user.roles],
        "scopes": [scope.name for role in user.roles for scope in role.scopes],
    }

    now = datetime.now(timezone.utc)

    data.update({"exp": now + access_token_delta})
    access_token = jwt.encode(data, SIGN_KEY, algorithm=SIGN_ALGORITHM)

    data.update({"exp": now + refresh_token_delta})
    refresh_token = jwt.encode(data, SIGN_KEY, algorithm=SIGN_ALGORITHM)

    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


def get_user(token: Annotated[str, Depends(oauth_scheme)], db: Annotated[Session, Depends(get_session)]) -> User:
    auth_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SIGN_KEY, algorithms=[SIGN_ALGORITHM])
        user_id: uuid.UUID = uuid.UUID(payload.get("sub"))
        if user_id is None:
            raise auth_exception
    except JWTError:
        raise auth_exception
    crud = GenericCRUD(db)
    user: Optional[User] = crud.read(User, ObjectIdentifier(id=user_id))
    if not user:
        raise auth_exception
    return user


class RoleValidator:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Annotated[User, Depends(get_user)]):
        if set([role.name for role in user.roles]) & set(self.allowed_roles):
            return True
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing permissions")


class ScopeValidator:
    registered_scopes: set[str] = set()

    def __init__(self, needed_scope: str):
        self.needed_scope = needed_scope
        self.registered_scopes.add(self.needed_scope)

    def __call__(self, user: Annotated[User, Depends(get_user)]):
        user_scopes = {scope.name for role in user.roles for scope in role.scopes}
        if self.needed_scope in user_scopes:
            return True
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Missing scope {self.needed_scope}')


def scope(needed_scope: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user: Depends(get_user), **kwargs):
            ScopeValidator(needed_scope)(user)
            return await func(*args, **kwargs)

        return wrapper

    return decorator
