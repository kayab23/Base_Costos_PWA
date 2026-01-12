"""Motor de cálculo para Landed Cost y Lista de Precios.

Usa los datos ya sincronizados en SQL Server y escribe los resultados en
LandedCostCache y ListaPrecios para el piloto.
"""
from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import pyodbc

DEFAULT_CONN_STR = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=.\\SQLEXPRESS;"
    "DATABASE=BD_Calculo_Costos;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

PRICE_MIN_MULTIPLIER = 1.10


def get_connection() -> pyodbc.Connection:
    conn_str = os.getenv("SQLSERVER_CONN", DEFAULT_CONN_STR)
    return pyodbc.connect(conn_str, autocommit=False)


def fetch_dicts(cursor: pyodbc.Cursor, query: str) -> List[Dict[str, Any]]:
    cursor.execute(query)
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def fetch_reference_data(cursor: pyodbc.Cursor) -> Dict[str, Any]:
    data = {}
    # Ahora los costos están en la tabla Productos
    data["productos"] = fetch_dicts(
        cursor,
        "SELECT sku, origen, moneda_base, costo_base, fecha_actualizacion FROM dbo.Productos",
    )
    data["parametros"] = fetch_dicts(
        cursor,
        "SELECT concepto, tipo, valor FROM dbo.ParametrosImportacion WHERE vigente_hasta IS NULL",
    )
    data["tipos_cambio"] = fetch_dicts(
        cursor,
        "SELECT moneda, tipo_cambio_mxn, fecha FROM dbo.TiposCambio",
    )
    # Tablas PoliticasMargen y Versiones eliminadas
    data["margenes"] = []
    return data


def normalize_number(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Decimal):
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


def build_cost_map(cost_rows: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    cost_map: Dict[str, Dict[str, Any]] = {}
    for row in cost_rows:
        sku = row["sku"].strip()
        fecha = row.get("fecha_actualizacion")
        prioridad = fecha or datetime.min
        if sku not in cost_map or prioridad >= (cost_map[sku].get("fecha_actualizacion") or datetime.min):
            cost_map[sku] = row
    return cost_map


def build_fx_map(fx_rows: Iterable[Dict[str, Any]]) -> Dict[str, float]:
    fx_map: Dict[str, Tuple[datetime, float]] = {}
    for row in fx_rows:
        moneda = (row["moneda"] or "MXN").strip().upper()
        fecha = row.get("fecha") or datetime.min
        valor = normalize_number(row.get("tipo_cambio_mxn"), 1.0)
        if moneda not in fx_map or fecha >= fx_map[moneda][0]:
            fx_map[moneda] = (fecha, valor)
    result = {moneda: valor for moneda, (_, valor) in fx_map.items()}
    result.setdefault("MXN", 1.0)
    return result


def split_parametros(param_rows: Iterable[Dict[str, Any]]) -> Tuple[Dict[str, float], Dict[str, float]]:
    porcentajes: Dict[str, float] = {}
    fijos: Dict[str, float] = {}
    for row in param_rows:
        concepto = (row["concepto"] or "").strip().lower()
        tipo = (row["tipo"] or "").strip().lower()
        valor = normalize_number(row.get("valor"), 0.0)
        if "fijo" in tipo:
            fijos[concepto] = valor
        else:
            porcentajes[concepto] = valor
    return porcentajes, fijos


def calculate_landed_costs(
    productos: Iterable[Dict[str, Any]],
    cost_map: Dict[str, Dict[str, Any]],
    fx_map: Dict[str, float],
    pct_params: Dict[str, float],
    fixed_params: Dict[str, float],
    transporte: str,
) -> List[Dict[str, Any]]:
    transporte_key = transporte.strip().lower()
    flete_pct = pct_params.get(transporte_key, 0.0)
    seguro_pct = pct_params.get("seguro", 0.0)
    arancel_pct = pct_params.get("arancel", 0.0)
    dta_pct = pct_params.get("dta", 0.0)
    honorarios_aduanales_pct = pct_params.get("honorarios_aduanales", 0.0)
    markup_pct = pct_params.get("mark_up", 0.1)  # 10% por defecto

    landed_rows: List[Dict[str, Any]] = []
    for producto in productos:
        sku = producto["sku"].strip()
        # Los costos ahora están directamente en productos
        costo_base = normalize_number(producto.get("costo_base"), 0.0)
        moneda_costo = (producto.get("moneda_base") or "MXN").strip().upper()
        tc = fx_map.get(moneda_costo, 1.0)
        costo_base_mxn = costo_base * tc

        origen = (producto.get("origen") or "").strip().lower()
        if origen == "importado":
            # Fórmula Excel: Costo_Base_MXN × (1 + Flete% + Seguro% + Arancel% + DTA% + Honorarios_Aduanales%)
            landed = costo_base_mxn * (1 + flete_pct + seguro_pct + arancel_pct + dta_pct + honorarios_aduanales_pct)
        else:
            landed = costo_base_mxn
        
        # Calcular Mark_up: Landed Cost × (1 + markup_pct)
        mark_up = landed * (1 + markup_pct)

        landed_rows.append(
            {
                "sku": sku,
                "transporte": transporte,
                "origen": producto.get("origen"),
                "moneda_base": moneda_costo,
                "costo_base": costo_base,
                "tc_mxn": tc,
                "costo_base_mxn": costo_base_mxn,
                "flete_pct": flete_pct,
                "seguro_pct": seguro_pct,
                "arancel_pct": arancel_pct,
                "dta_pct": dta_pct,
                "honorarios_aduanales_pct": honorarios_aduanales_pct,
                "gastos_aduana_mxn": 0.0,  # Ya no se usa este concepto
                "landed_cost_mxn": landed,
                "mark_up": mark_up,
                "calculado_en": datetime.now(timezone.utc),
            }
        )
    return landed_rows


def calculate_price_list(
    landed_rows: Iterable[Dict[str, Any]],
    margenes: Iterable[Dict[str, Any]],
    fx_map: Dict[str, float],
    monedas_precio: Sequence[str],
) -> List[Dict[str, Any]]:
    price_rows: List[Dict[str, Any]] = []
    for landed in landed_rows:
        sku = landed["sku"]
        landed_cost = landed["landed_cost_mxn"]
        for margen_row in margenes:
            tipo_cliente = margen_row["tipo_cliente"].strip()
            margen = normalize_number(margen_row.get("margen"), 0.0)
            divisor = max(1.0 - margen, 1e-9)
            precio_mxn = landed_cost / divisor if landed_cost else 0.0
            precio_min_mxn = landed_cost * PRICE_MIN_MULTIPLIER

            for moneda in monedas_precio:
                moneda_norm = moneda.strip().upper()
                tc = fx_map.get(moneda_norm, 1.0)
                precio_moneda = precio_mxn / tc if tc else None
                price_rows.append(
                    {
                        "sku": sku,
                        "tipo_cliente": tipo_cliente,
                        "moneda_precio": moneda_norm,
                        "tc_mxn": tc,
                        "landed_cost_mxn": landed_cost,
                        "margen_pct": margen,
                        "precio_venta_mxn": precio_mxn,
                        "precio_venta_moneda": precio_moneda,
                        "precio_min_mxn": precio_min_mxn,
                        "notas": None,
                        "version_id": version_id,
                        "calculado_en": datetime.now(timezone.utc),
                    }
                )
    return price_rows


def persist_rows(
    cursor: pyodbc.Cursor,
    table: str,
    columns: Sequence[str],
    rows: Iterable[Dict[str, Any]],
    transporte: str | None = None,
) -> None:
    rows = list(rows)
    print(f"{table}: escribiendo {len(rows)} filas")
    # Si es LandedCostCache, solo eliminar registros del transporte específico
    if table == "dbo.LandedCostCache" and transporte:
        cursor.execute(f"DELETE FROM {table} WHERE transporte = ?", transporte)
        print(f"  (eliminados registros existentes de transporte: {transporte})")
    else:
        cursor.execute(f"DELETE FROM {table}")
    if not rows:
        return
    placeholders = ",".join(["?"] * len(columns))
    sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
    payload: List[Tuple[Any, ...]] = [tuple(row.get(col) for col in columns) for row in rows]
    cursor.fast_executemany = True
    cursor.executemany(sql, payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calcula Landed Cost y Lista de Precios")
    parser.add_argument("--transporte", default="Maritimo", help="Clave del modo de transporte en Parametros")
    parser.add_argument(
        "--moneda-precio",
        action="append",
        dest="monedas",
        help="Moneda destino para precios (por defecto solo MXN). Puedes repetir la bandera.",
    )
    return parser.parse_args()


def run_calculations(
    transporte: str,
    monedas_precio: Sequence[str] | None = None,
    conn: pyodbc.Connection | None = None,
) -> Dict[str, Any]:
    monedas = list(monedas_precio or ["MXN"])
    own_connection = False
    if conn is None:
        conn = get_connection()
        own_connection = True

    try:
        cursor = conn.cursor()
        data = fetch_reference_data(cursor)
        # Ya no necesitamos build_cost_map porque los costos están en productos
        fx_map = build_fx_map(data["tipos_cambio"])
        pct_params, fixed_params = split_parametros(data["parametros"])

        landed_rows = calculate_landed_costs(
            data["productos"],
            {},  # cost_map ya no se usa
            fx_map,
            pct_params,
            fixed_params,
            transporte,
        )

        persist_rows(
            cursor,
            "dbo.LandedCostCache",
            [
                "sku",
                "transporte",
                "origen",
                "moneda_base",
                "costo_base",
                "tc_mxn",
                "costo_base_mxn",
                "flete_pct",
                "seguro_pct",
                "arancel_pct",
                "dta_pct",
                "honorarios_aduanales_pct",
                "gastos_aduana_mxn",
                "landed_cost_mxn",
                "mark_up",
                "calculado_en",
            ],
            landed_rows,
            transporte,  # Pasar el transporte para eliminar solo ese tipo
        )

        conn.commit()
        summary = {
            "landed_rows": len(landed_rows),
            "price_rows": 0,
            "version_id": data.get("version_id"),
        }
        print(
            f"\n✅ Cálculos almacenados correctamente. Landed={summary['landed_rows']}"
        )
        return summary
    finally:
        if own_connection:
            conn.close()


def main() -> None:
    args = parse_args()
    run_calculations(args.transporte, args.monedas)


if __name__ == "__main__":
    main()
