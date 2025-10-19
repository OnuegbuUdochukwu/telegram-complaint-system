from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
from dotenv import dotenv_values

config = dotenv_values("../.env")
DATABASE_URL = config.get("DATABASE_URL") or "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, echo=False)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

def init_db() -> None:
    SQLModel.metadata.create_all(engine)
