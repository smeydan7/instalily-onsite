"""Application settings, loaded from environment / .env."""
from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Roofing Sales Intelligence"
    environment: str = "local"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+psycopg://sales:sales@localhost:5432/sales_intel"

    backend_cors_origins: list[str] = ["http://localhost:5173"]

    # --- GAF / Coveo data source ---
    # These are the public search tokens GAF's own frontend ships to browsers, so
    # they are not secrets in the usual sense. Kept in config (not hardcoded) so they
    # can be rotated or overridden per environment without touching code.
    coveo_org_id: str = "gafmaterialscorporationproduction3yalqk12"
    coveo_api_key: str = "xx3cfe6ca4-11f2-45b6-83ad-41e053e06504"
    coveo_default_zip: str = "10013"
    coveo_default_radius_miles: int = 25
    coveo_timeout_seconds: float = 15.0

    # Optional Google Geocoding key. When set, ZIPs are geocoded via Google (matching
    # GAF's own geocoder exactly). Without it we use offline pgeocode + a curated
    # override table. See app/integrations/gaf_coveo.py.
    google_maps_api_key: str = ""

    # Distributor branch/territory ZIPs the GAF pipeline ingests by default.
    # Override per run via the pipeline request config.
    gaf_territory_zips: list[str] = ["10013", "90210", "60601"]

    # Dev convenience: create tables on startup instead of running Alembic.
    # Production uses migrations — see PLAN.md.
    auto_create_tables: bool = True

    @field_validator("gaf_territory_zips", mode="before")
    @classmethod
    def _split_zips(cls, v: object) -> object:
        if isinstance(v, str):
            return [z.strip() for z in v.split(",") if z.strip()]
        return v

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v: object) -> object:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


settings = Settings()
