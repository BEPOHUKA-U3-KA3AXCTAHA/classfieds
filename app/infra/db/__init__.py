"""DB infrastructure: engine, Base, session, transactions, migrations.

Re-exports the engine module so all code can keep using `from app.infra.db import Base`.
Migrations live in the sibling `migrations/` folder (Alembic).
"""
from app.infra.db.engine import Base, engine, SessionLocal, transaction, session_factory

__all__ = ["Base", "engine", "SessionLocal", "transaction", "session_factory"]
