"""Shared API dependencies."""
from __future__ import annotations

from app.db.session import get_db  # re-exported for endpoint imports

__all__ = ["get_db"]
