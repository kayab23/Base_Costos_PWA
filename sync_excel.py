"""Sincroniza Plantilla_Pricing_Costos_Importacion.xlsx hacia SQL Server.

Requisitos:
- py -m pip install openpyxl pyodbc python-dotenv (opcional)
- Driver ODBC 18 para SQL Server.
- Variable de entorno SQLSERVER_CONN o ajusta DEFAULT_CONN_STR.
"""
from __future__ import annotations

import os
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import pyodbc
from openpyxl import load_workbook

FILE_NAME = "Plantilla_Pricing_Costos_Importacion.xlsx"
DEFAULT_CONN_STR = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=BD_Calculo_Costos;"
    "UID=sa;PWD=YourStrongPassword!;"
    "TrustServerCertificate=yes;"
)


def to_decimal(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if not cleaned:
            return default
        try:
            return float(cleaned)
        except ValueError:
            return default
    return default


def bool_from_str(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"si", "sí", "yes", "y"}:
            return 1
        if normalized in {"no", "n"}:
            return 0
    return 0


def register_version(cursor: pyodbc.Cursor, nombre: str, descripcion: str) -> int:
    row = cursor.execute(
        """
        INSERT INTO dbo.Versiones (nombre, descripcion, creado_por, fuente)
        OUTPUT INSERTED.version_id
        VALUES (?, ?, ?, ?)
        """,
        nombre,
        descripcion,
        "sync_excel.py",
        "excel",
    ).fetchone()
    return int(row[0])


def bulk_insert(
    cursor: pyodbc.Cursor,
    table: str,
    columns: Sequence[str],
    rows: Iterable[Dict[str, Any]],
) -> None:
    rows = list(rows)
    print(f"{table}: {len(rows)} registros")
    if not rows:
        return
    placeholders = ",".join(["?"] * len(columns))
    sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
    payload: List[Tuple[Any, ...]] = [tuple(row.get(col) for col in columns) for row in rows]
    cursor.fast_executemany = True
    cursor.executemany(sql, payload)


def clear_tables(cursor: pyodbc.Cursor, tables: Sequence[str]) -> None:
    for table in tables:
        cursor.execute(f"DELETE FROM {table}")


def read_catalogo(ws, version_id: int) -> List[Dict[str, Any]]:
    rows = []
    for sku, descripcion, proveedor, modelo, origen, categoria, unidad, moneda, activo, *_ in ws.iter_rows(min_row=2, values_only=True):
        if not sku:
            continue
        rows.append(
            {
                "sku": sku.strip(),
                "descripcion": descripcion or "",
                "proveedor": proveedor,
                "modelo": modelo,
                "origen": origen,
                "categoria": categoria,
                "unidad": unidad,
                "moneda_base": (moneda or "USD").strip(),
                "activo": bool_from_str(activo),
                "notas": None,
                "version_id": version_id,
            }
        )
    return rows


def read_costos(ws, version_id: int) -> List[Dict[str, Any]]:
    rows = []
    for sku, costo_base, moneda, fecha_act, notas, proveedor, *_ in ws.iter_rows(min_row=2, values_only=True):
        if not sku:
            continue
        rows.append(
            {
                "sku": sku.strip(),
                "costo_base": to_decimal(costo_base),
                "moneda": (moneda or "USD").strip(),
                "fecha_actualizacion": fecha_act.date() if hasattr(fecha_act, "date") else fecha_act,
                "notas": notas,
                "proveedor": proveedor,
                "version_id": version_id,
            }
        )
    return rows


def read_parametros(ws, version_id: int) -> List[Dict[str, Any]]:
    rows = []
    for concepto, tipo, valor, descripcion, _, nota, _ in ws.iter_rows(min_row=2, values_only=True):
        if not concepto:
            continue
        rows.append(
            {
                "concepto": concepto.strip(),
                "tipo": (tipo or "%").strip(),
                "valor": to_decimal(valor, 0.0) or 0.0,
                "descripcion": descripcion,
                "notas": nota,
                "vigente_desde": datetime.utcnow().date(),
                "vigente_hasta": None,
                "version_id": version_id,
            }
        )
    return rows


def read_tipos_cambio(ws, version_id: int) -> List[Dict[str, Any]]:
    rows = []
    for moneda, tc_mxn, fuente, fecha in ws.iter_rows(min_row=2, values_only=True):
        if not moneda or not tc_mxn:
            continue
        fecha_val = fecha.date() if hasattr(fecha, "date") else datetime.utcnow().date()
        rows.append(
            {
                "moneda": moneda.strip(),
                "fecha": fecha_val,
                "tipo_cambio_mxn": to_decimal(tc_mxn, 0.0) or 0.0,
                "fuente": fuente or "Manual",
                "version_id": version_id,
            }
        )
    return rows


def read_margenes(ws, version_id: int) -> List[Dict[str, Any]]:
    rows = []
    for tipo_cliente, margen, notas in ws.iter_rows(min_row=2, values_only=True):
        if not tipo_cliente or margen is None:
            continue
        rows.append(
            {
                "tipo_cliente": tipo_cliente.strip(),
                "margen": to_decimal(margen, 0.0) or 0.0,
                "notas": notas,
                "vigente_desde": datetime.utcnow().date(),
                "vigente_hasta": None,
                "version_id": version_id,
            }
        )
    return rows


def read_control_versiones(ws) -> List[Dict[str, Any]]:
    rows = []
    for fecha, version, cambio, responsable in ws.iter_rows(min_row=2, values_only=True):
        if not fecha and not version:
            continue
        fecha_val = fecha if fecha else datetime.utcnow()
        rows.append(
            {
                "fecha": fecha_val,
                "version": version or "",
                "cambio": cambio or "",
                "responsable": responsable or "",
            }
        )
    return rows


def main() -> None:
    conn_str = os.getenv("SQLSERVER_CONN", DEFAULT_CONN_STR)
    wb = load_workbook(FILE_NAME, data_only=True)

    control_sheet = wb["CONTROL_VERSIONES"] if "CONTROL_VERSIONES" in wb.sheetnames else None
    sheets = {
        "catalogo": wb["CATALOGO_PRODUCTOS"],
        "costos": wb["COSTO_BASE"],
        "parametros": wb["PARAMETROS_IMPORTACION"],
        "tipos_cambio": wb["TIPOS_CAMBIO"],
        "margenes": wb["POLITICAS_MARGEN"] if "POLITICAS_MARGEN" in wb.sheetnames else None,
        "control": control_sheet,
    }

    with pyodbc.connect(conn_str, autocommit=False) as conn:
        cursor = conn.cursor()
        version_name = datetime.utcnow().strftime("excel-%Y%m%d-%H%M%S")
        version_id = register_version(cursor, version_name, "Carga desde Excel piloto")

        catalog_rows = read_catalogo(sheets["catalogo"], version_id)
        cost_rows = read_costos(sheets["costos"], version_id)
        param_rows = read_parametros(sheets["parametros"], version_id)
        fx_rows = read_tipos_cambio(sheets["tipos_cambio"], version_id)
        margin_rows = read_margenes(sheets["margenes"], version_id) if sheets["margenes"] else []
        control_rows = read_control_versiones(sheets["control"]) if sheets["control"] else []

        clear_tables(cursor, [
            "dbo.ControlVersiones",
            "dbo.PoliticasMargen",
            "dbo.TiposCambio",
            "dbo.ParametrosImportacion",
            "dbo.CostosBase",
            "dbo.Productos",
        ])

        bulk_insert(cursor, "dbo.Productos", [
            "sku",
            "descripcion",
            "proveedor",
            "modelo",
            "origen",
            "categoria",
            "unidad",
            "moneda_base",
            "activo",
            "notas",
            "version_id",
        ], catalog_rows)

        bulk_insert(cursor, "dbo.CostosBase", [
            "sku",
            "costo_base",
            "moneda",
            "fecha_actualizacion",
            "notas",
            "proveedor",
            "version_id",
        ], cost_rows)

        bulk_insert(cursor, "dbo.ParametrosImportacion", [
            "concepto",
            "tipo",
            "valor",
            "descripcion",
            "notas",
            "vigente_desde",
            "vigente_hasta",
            "version_id",
        ], param_rows)

        bulk_insert(cursor, "dbo.TiposCambio", [
            "moneda",
            "fecha",
            "tipo_cambio_mxn",
            "fuente",
            "version_id",
        ], fx_rows)

        bulk_insert(cursor, "dbo.PoliticasMargen", [
            "tipo_cliente",
            "margen",
            "notas",
            "vigente_desde",
            "vigente_hasta",
            "version_id",
        ], margin_rows)

        if control_rows:
            bulk_insert(cursor, "dbo.ControlVersiones", [
                "fecha",
                "version",
                "cambio",
                "responsable",
            ], control_rows)

        conn.commit()
        print(f"Sincronización completada. Version ID: {version_id}")


if __name__ == "__main__":
    main()
