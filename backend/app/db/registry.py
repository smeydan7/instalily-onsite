"""Single import point that pulls in all ORM models.

Import this (not individual model modules) wherever `Base.metadata` must be complete
— e.g. Alembic's env.py.
"""
from app.db.base import Base  # noqa: F401
from app.models.account import Account  # noqa: F401
from app.models.contact import Contact  # noqa: F401
from app.models.data_source import DataSource, IngestionRun  # noqa: F401
from app.models.insight import Insight  # noqa: F401
from app.models.lead import Lead  # noqa: F401
