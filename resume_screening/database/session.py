from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

from resume_screening.config import settings


def build_engine():
    # SQLite needs this flag for multithreaded Streamlit usage.
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    return create_engine(settings.database_url, echo=False, connect_args=connect_args)


engine = build_engine()


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)

