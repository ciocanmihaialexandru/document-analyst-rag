"""Conexiunea la Postgres: engine, sesiuni, tranzacții."""

import os
from contextlib import contextmanager
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


@contextmanager
def transaction() -> Generator[Session, None, None]:
    """Context manager pentru tranzacții atomice (commit sau rollback)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()