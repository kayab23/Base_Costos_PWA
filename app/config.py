"""Configuración básica del backend."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from cost_engine import DEFAULT_CONN_STR


@dataclass
class Settings:
    sqlserver_conn: str = field(
        default_factory=lambda: os.getenv("SQLSERVER_CONN", DEFAULT_CONN_STR)
    )
    default_transporte: str = "Maritimo"
    default_monedas: list[str] = field(default_factory=lambda: ["MXN"])
    allowed_origins: list[str] = field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )
    api_title: str = "Base Costos API"
    api_version: str = "0.1.0"


settings = Settings()
