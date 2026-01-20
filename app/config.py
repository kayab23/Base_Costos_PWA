
from __future__ import annotations
import os
from dataclasses import dataclass, field
from cost_engine import DEFAULT_CONN_STR
from dotenv import load_dotenv
load_dotenv()


@dataclass
class Settings:
    sqlserver_conn: str = field(
        default_factory=lambda: os.getenv("SQLSERVER_CONN") or (
            "DRIVER={ODBC Driver 18 for SQL Server};SERVER=" +
            os.getenv('DATABASE_SERVER', 'localhost\\SQLEXPRESS') +
            ";DATABASE=" + os.getenv('DATABASE_NAME', 'BD_Calculo_Costos') +
            ";Trusted_Connection=yes;TrustServerCertificate=yes;"
        )
    )
    default_transporte: str = os.getenv("DEFAULT_TRANSPORTE", "Maritimo")
    default_monedas: list[str] = field(default_factory=lambda: os.getenv("DEFAULT_MONEDAS", "MXN").split(","))
    allowed_origins: list[str] = field(default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","))
    api_title: str = os.getenv("API_TITLE", "Base Costos API")
    api_version: str = os.getenv("API_VERSION", "0.1.0")
    secret_key: str = os.getenv("SECRET_KEY", "cambiar-por-secreto-en-produccion")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/app.log")
    environment: str = os.getenv("ENVIRONMENT", "development")

settings = Settings()
