import uuid

from sqlmodel import Field, SQLModel


class ObjectIdentifier(SQLModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    def __str__(self):
        return str(self.id)
