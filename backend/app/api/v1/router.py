"""Aggregate all v1 endpoint routers."""
from __future__ import annotations

from fastapi import APIRouter

from app.api import datasource
from app.api.v1.endpoints import accounts, health, insights, leads, pipeline

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(accounts.router)
api_router.include_router(leads.router)
api_router.include_router(insights.router)
api_router.include_router(pipeline.router)
api_router.include_router(datasource.router)  # /gaf-contractors
