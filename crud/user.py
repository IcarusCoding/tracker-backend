import uuid
from typing import Optional, Sequence

from passlib.context import CryptContext
from sqlmodel import Session, select

from models import User, UserUpdate, UserLogin

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_user(db: Session, user: User) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: uuid.UUID) -> Optional[User]:
    return db.get(User, user_id)


def get_user_by_name(db: Session, name: str) -> Optional[User]:
    return db.exec(select(User).where(User.name == name)).first()


def get_users(db: Session, skip: int = 0, limit: int = 10) -> Sequence[User]:
    return db.exec(select(User).offset(skip).limit(limit)).all()


def update_user(db: Session, user_id: uuid.UUID, user_update: UserUpdate) -> Optional[User]:
    user = db.get(User, user_id)
    if not user:
        return None

    update_data = user_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(user, key, value)

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def delete_user(db: Session, user_id: uuid.UUID) -> None:
    user = db.get(User, user_id)
    if user:
        db.delete(user)
        db.commit()


def validate_auth(db: Session, user_login: UserLogin) -> Optional[User]:
    user = db.exec(select(User).where(User.name == user_login.name)).first()

    if user and pwd_context.verify(user_login.password, user.password):
        return user

    return None
