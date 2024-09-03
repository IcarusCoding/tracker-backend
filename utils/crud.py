from typing import TypeVar, Generic, Type, Optional, Sequence

from sqlmodel import Session, SQLModel, select

from utils.models import ObjectIdentifier

T = TypeVar('T', bound=SQLModel)


class GenericCRUD(Generic[T]):

    def __init__(self, model: Type[T], session: Session):
        self.model = model
        self.session = session

    def create(self, **kwargs) -> T:
        obj = self.model(**kwargs)
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def read(self, obj_id: ObjectIdentifier) -> Optional[T]:
        return self.session.get(self.model, obj_id.id)

    def read_all(self, skip: int, limit: int) -> Sequence[T]:
        return self.session.exec(select(self.model).offset(skip).limit(limit)).all()

    def update(self, obj_id: ObjectIdentifier, **kwargs) -> Optional[T]:
        obj = self.session.get(self.model, obj_id.id)
        if obj is None:
            return None
        obj = self.model(**kwargs)
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def delete(self, obj_id: ObjectIdentifier) -> None:
        obj = self.session.get(self.model, obj_id.id)
        if obj:
            self.session.delete(obj)
            self.session.commit()
