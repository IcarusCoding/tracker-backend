from typing import TypeVar, Generic, Type, Optional, Sequence

from sqlalchemy import Select
from sqlmodel import Session, SQLModel, select

from utils.models import ObjectIdentifier

T = TypeVar('T', bound=SQLModel)


class GenericCRUD(Generic[T]):
    __FILTERS = {
        "gt": lambda column: column.__gt__,
        "lt": lambda column: column.__lt__,
        "ge": lambda column: column.__ge__,
        "le": lambda column: column.__le__,
        "ne": lambda column: column.__ne__,
        "is": lambda column: column.__eq__,
        "is_not": lambda column: column.is_not,
    }

    def __init__(self, session: Session):
        self.session = session

    def __create_filter(self, model: Type[T], **kwargs):
        filters = []
        for k, v in kwargs.items():
            if "___" in k:
                field, operator = k.split("___", 1)
                column = getattr(model, field, None)
                if not column:
                    raise ValueError(f"Column {field} is not defined")
                sql_filter = self.__FILTERS.get(operator)
                if sql_filter:
                    filters.append(sql_filter(column)(v))
            else:
                column = getattr(model, k, None)
                if column:
                    filters.append(column == v)
        return filters

    def create(self, model: Type[T], **kwargs) -> T:
        obj = model(**kwargs)
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def read(self, model: Type[T], obj_id: ObjectIdentifier) -> Optional[T]:
        return self.session.get(model, obj_id.id)

    def read_raw(self, model: Type[T], **kwargs) -> Optional[T]:
        filters = self.__create_filter(model, **kwargs)
        sel: Select = select(model).filter(*filters).limit(1)
        return self.session.exec(sel).first()

    def read_all(self, model: Type[T], skip: int, limit: int) -> Sequence[T]:
        return self.session.exec(select(model).offset(skip).limit(limit)).all()

    def update(self, model: Type[T], obj_id: ObjectIdentifier, **kwargs) -> Optional[T]:
        obj = self.session.get(model, obj_id.id)
        if obj is None:
            return None

        for key, value in kwargs.items():
            if not value:
                continue
            setattr(obj, key, value)

        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def delete(self, model: Type[T], obj_id: ObjectIdentifier) -> None:
        obj = self.session.get(model, obj_id.id)
        if obj:
            self.session.delete(obj)
            self.session.commit()

# TODO add transaction rollback support by not commiting directly
    def delete_raw(self, model: Type[T], **kwargs) -> None:
        filters = self.__create_filter(model, **kwargs)
        sel: Select = select(model).filter(*filters)
        result = self.session.exec(sel).all()

        for obj in result:
            self.session.delete(obj)

        self.session.commit()


    def refresh(self, obj: T) -> None:
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)

    def exists(self, model: Type[T], **kwargs) -> bool:
        filters = self.__create_filter(model, **kwargs)
        sel: Select = select(model).filter(*filters).limit(1)
        return self.session.exec(sel).first() is not None
