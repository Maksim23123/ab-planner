from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.engine import URL, create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()

def ensure_database():
    url = URL.create(
        "postgresql",
        username=settings.db_user,
        password=settings.db_password,
        host=settings.db_host,
        port=settings.db_port,
        database="postgres", # maintenance DB
    )
    engine = create_engine(url, isolation_level="AUTOCOMMIT")
    with engine.begin() as conn:
        exists = conn.scalar(text("SELECT 1 FROM pg_database WHERE datname=:name"), {"name": settings.db_name})
        if not exists:
            conn.execute(text(f'CREATE DATABASE \"{settings.db_name}\"'))


TARGET_URL = URL.create(
    "postgresql",
    username=settings.db_user,
    password=settings.db_password,
    host=settings.db_host,
    port=settings.db_port,
    database=settings.db_name
)
engine = create_engine(TARGET_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)