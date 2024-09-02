import uuid
from typing import Optional, Type, TypeVar

from sqlmodel import Session, SQLModel, select

T = TypeVar("T", bound=SQLModel)


def create(db: Session, model: Type[T], **kwargs) -> T:
    obj = model(**kwargs)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, model: Type[T], obj_id: uuid.UUID) -> None:
    obj = db.get(model, obj_id)
    if obj:
        db.delete(obj)
        db.commit()


def get(db: Session, model: Type[T], obj_id: uuid.UUID) -> Optional[T]:
    return db.get(model, obj_id)


def get_by_name(db: Session, model: Type[T], name: str) -> Optional[T]:
    return db.exec(select(model).where(model.name == name)).first()


def refresh(db: Session, parent: T) -> None:
    db.add(parent)
    db.commit()
    db.refresh(parent)
