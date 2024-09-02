import uuid
from datetime import datetime

from passlib.context import CryptContext
from pydantic import field_validator
from sqlmodel import SQLModel, Field, Relationship

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RoleScopeLink(SQLModel, table=True):
    role_id: uuid.UUID = Field(foreign_key="role.id", primary_key=True)
    scope_id: uuid.UUID = Field(foreign_key="scope.id", primary_key=True)

class Scope(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=50, unique=True)
    roles: list["Role"] = Relationship(back_populates="scopes", link_model=RoleScopeLink)

class ScopeCreate(SQLModel):
    name: str

class UserRoleLink(SQLModel, table=True):
    user_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True)
    role_id: uuid.UUID = Field(foreign_key="role.id", primary_key=True)


class Role(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=50, unique=True)
    scopes: list["Scope"] = Relationship(back_populates="roles", link_model=RoleScopeLink)
    users: list["User"] = Relationship(back_populates="roles", link_model=UserRoleLink)


class RoleCreate(SQLModel):
    name: str


class UserBase(SQLModel):
    name: str = Field(max_length=30, index=True, unique=True)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created: datetime = Field(default_factory=datetime.now, nullable=False)
    password: str = Field()
    roles: list[Role] = Relationship(back_populates="users", link_model=UserRoleLink)
    devices: list["Device"] = Relationship(back_populates="user", cascade_delete=True)

    @field_validator('password')
    def hash_password(cls, value: str) -> str:
        return pwd_context.hash(value)

    class Config:
        validate_assignment = True


class UserRead(UserBase):
    id: uuid.UUID
    created: datetime
    roles: list[Role]


class UserUpdate(SQLModel):
    name: str
    password: str

    @field_validator('password')
    def hash_password(cls, value: str) -> str:
        return pwd_context.hash(value)

    class Config:
        validate_assignment = True


class UserLogin(SQLModel):
    name: str
    password: str


class UserCreate(UserLogin):
    pass

