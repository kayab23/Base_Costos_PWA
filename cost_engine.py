"""Motor de cálculo para Landed Cost y Listas de Precios.

Este módulo es el núcleo del sistema de cálculo de precios. Realiza:

1. CÁLCULO DE LANDED COST:
   - Lee costos base de productos desde dbo.Productos
   - Aplica tasas de cambio desde dbo.TiposCambio
   - Agrega costos de importación según tipo de transporte:
     * Aéreo: +10% flete, +seguros, +aranceles, +DTA, +honorarios aduanales
     * Marítimo: +5% flete, +seguros, +aranceles, +DTA, +honorarios aduanales
   - Calcula Mark-up (Landed Cost × 1.10)
   - Guarda resultados en dbo.LandedCostCache

2. CÁLCULO DE LISTAS DE PRECIOS (4 NIVELES JERÁRQUICOS):
   - Precio Máximo = Mark-up × 2
   - Vendedor: 20% descuento (Precio Máx × 0.80)
   - Gerencia Comercial: 25% descuento (Precio Máx × 0.75)
   - Subdirección: 30% descuento (Precio Máx × 0.70)
   - Dirección: 35% descuento (Precio Máx × 0.65)
   - Guarda resultados en dbo.PreciosCalculados

Ejecución:
  python cost_engine.py --transporte Maritimo
  python cost_engine.py --transporte Aereo

Nota: Los cálculos son incrementales por tipo de transporte (no se eliminan
datos de otros transportes al recalcular).
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
        "SELECT sku, origen, categoria, moneda_base, costo_base, fecha_actualizacion FROM dbo.Productos",
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

        # Obtener categoría del producto
        categoria = (producto.get("categoria") or "").strip().lower()
        # Solo aplica flete si es equipo o insumo
        if categoria in ["equipo", "insumo"]:
            if transporte_key == "aereo":
                flete_pct = 0.10  # 10% para transporte Aéreo
            elif transporte_key == "maritimo":
                flete_pct = 0.05  # 5% para transporte Marítimo
            else:
                flete_pct = 0.0
        else:
            flete_pct = 0.0  # Otras categorías no pagan flete

        origen = (producto.get("origen") or "").strip().lower()
        if origen == "importado":
            # Fórmula: Costo_Base_MXN × (1 + Flete% + Seguro% + Arancel% + DTA% + Honorarios_Aduanales%)
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
                "categoria": categoria,
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


def calculate_price_lists(cursor, transporte: str) -> List[Dict[str, Any]]:
    """
    Calcula las 3 listas de precios con rangos según la jerarquía:
    - Vendedor: 90% a 65% sobre Mark-up
    - Gerencia Comercial: 65% a 40% sobre Mark-up
    - Gerencia: 40% a 10% sobre Mark-up (Mark-up base)
    """
    # Obtener listas de precios configuradas
    cursor.execute(
        """
        SELECT nombre_lista, margen_min_pct, margen_max_pct, orden_jerarquia
        FROM ListasPrecios
        WHERE activa = 1
        ORDER BY orden_jerarquia DESC
        """
    )
    listas = cursor.fetchall()
    
    if not listas:
        print("⚠️ No hay listas de precios configuradas")
        return []
    
    # Obtener datos de landed cost y mark_up
    cursor.execute(
        """
        SELECT sku, transporte, landed_cost_mxn, mark_up, 
               costo_base_mxn, flete_pct, seguro_pct, arancel_pct, dta_pct, 
               honorarios_aduanales_pct, categoria
        FROM LandedCostCache
        WHERE transporte = ?
        """,
        transporte,
    )
    landed_data = cursor.fetchall()
    
    if not landed_data:
        print(f"⚠️ No hay datos de Landed Cost para transporte {transporte}")
        return []
    
    # Obtener markup_pct de parámetros
    cursor.execute(
        "SELECT valor FROM ParametrosImportacion WHERE concepto = 'Mark_up'"
    )
    row = cursor.fetchone()
    markup_pct = float(row[0]) if row else 0.10
    
    price_rows: List[Dict[str, Any]] = []
    
    for item in landed_data:
        sku = item[0]
        trans = item[1]
        landed_cost = float(item[2]) if item[2] is not None else 0.0
        precio_base = float(item[3]) if item[3] is not None else 0.0  # Mark-up ya calculado
        costo_base_mxn = float(item[4]) if item[4] is not None else 0.0
        flete_pct = float(item[5]) if item[5] is not None else 0.0
        seguro_pct = float(item[6]) if item[6] is not None else 0.0
        arancel_pct = float(item[7]) if item[7] is not None else 0.0
        dta_pct = float(item[8]) if item[8] is not None else 0.0
        honorarios_aduanales_pct = float(item[9]) if item[9] is not None else 0.0
        categoria = item[10] if item[10] else ""
        
        # Nueva lógica de precios:
        # Precio Máximo = Mark-up × 2
        precio_maximo = precio_base * 2
        
        # Vendedor: 20% descuento del Precio Máximo
        precio_vendedor_min = precio_maximo * 0.80
        
        # Gerente Comercial: 25% descuento del Precio Máximo
        precio_gerente_com_min = precio_maximo * 0.75
        
        # Subdirección: 30% descuento del Precio Máximo
        precio_subdireccion_min = precio_maximo * 0.70
        
        # Dirección: 35% descuento del Precio Máximo
        precio_direccion_min = precio_maximo * 0.65
        
        price_rows.append({
            "sku": sku,
            "transporte": trans,
            "landed_cost_mxn": landed_cost,
            "precio_base_mxn": precio_base,
            "precio_maximo": precio_maximo,
            "precio_vendedor_min": precio_vendedor_min,
            "precio_gerente_com_min": precio_gerente_com_min,
            "precio_subdireccion_min": precio_subdireccion_min,
            "precio_direccion_min": precio_direccion_min,
            "markup_pct": markup_pct,
            "costo_base_mxn": costo_base_mxn,
            "flete_pct": flete_pct,
            "seguro_pct": seguro_pct,
            "arancel_pct": arancel_pct,
            "dta_pct": dta_pct,
            "honorarios_aduanales_pct": honorarios_aduanales_pct,
            "categoria": categoria,
            "fecha_calculo": datetime.now(timezone.utc),
        })
    
    return price_rows


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
                        # "version_id": version_id,  # Eliminado: variable no definida
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
    """Persiste filas en una tabla, eliminando datos existentes según la estrategia.
    
    Args:
        cursor: Cursor de pyodbc para ejecutar queries
        table: Nombre completo de la tabla (ej: 'dbo.LandedCostCache')
        columns: Lista de nombres de columnas a insertar
        rows: Diccionarios con los datos a insertar
        transporte: Tipo de transporte ('Aereo' o 'Maritimo')
    
    Estrategia de eliminación:
    - Para LandedCostCache y PreciosCalculados: Solo elimina registros del
      transporte específico para permitir cálculos incrementales por tipo
      de transporte sin afectar los datos de otros transportes.
    - Para otras tablas: Limpia completamente la tabla antes de insertar.
    
    Usa fast_executemany para inserción masiva eficiente.
    """
    rows = list(rows)
    print(f"{table}: escribiendo {len(rows)} filas")
    
    # Si es LandedCostCache o PreciosCalculados, solo eliminar registros del transporte específico
    # Esto permite recalcular Marítimo sin afectar Aéreo y viceversa
    if table in ["dbo.LandedCostCache", "dbo.PreciosCalculados"] and transporte:
        cursor.execute(f"DELETE FROM {table} WHERE transporte = ?", transporte)
        print(f"  (eliminados registros existentes de transporte: {transporte})")
    else:
        # Para otras tablas, limpieza completa
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
                "categoria",
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

        # Calcular listas de precios
        print(f"\n📊 Calculando listas de precios para {transporte}...")
        price_rows = calculate_price_lists(cursor, transporte)
        
        if price_rows:
            persist_rows(
                cursor,
                "dbo.PreciosCalculados",
                [
                    "sku",
                    "transporte",
                    "landed_cost_mxn",
                    "precio_base_mxn",
                    "precio_maximo",
                    "precio_vendedor_min",
                    "precio_gerente_com_min",
                    "precio_subdireccion_min",
                    "precio_direccion_min",
                    "markup_pct",
                    "costo_base_mxn",
                    "flete_pct",
                    "seguro_pct",
                    "arancel_pct",
                    "dta_pct",
                    "honorarios_aduanales_pct",
                    "categoria",
                    "fecha_calculo",
                ],
                price_rows,
                transporte,
            )

        conn.commit()
        summary = {
            "landed_rows": len(landed_rows),
            "price_rows": len(price_rows) if price_rows else 0,
            # "version_id": data.get("version_id"),  # Eliminado: ya no existe version_id
        }
        print(
            f"\n✅ Cálculos almacenados correctamente. Landed={summary['landed_rows']}, Precios={summary['price_rows']}"
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
