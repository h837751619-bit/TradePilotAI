from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def make_session_factory(database_url: str) -> sessionmaker[Session]:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine_options = {"connect_args": connect_args}
    if database_url == "sqlite:///:memory:":
        engine_options["poolclass"] = StaticPool
    engine = create_engine(database_url, **engine_options)
    # SQLite create_all keeps lightweight local/test workflows convenient.
    # Server databases are schema-managed exclusively by Alembic migrations.
    if database_url.startswith("sqlite"):
        Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session(factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    with factory() as session:
        yield session
