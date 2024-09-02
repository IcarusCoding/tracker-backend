from sqlmodel import SQLModel, create_engine

DATABASE_URL = "sqlite:///./sql_app.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_database():
    SQLModel.metadata.create_all(engine)
