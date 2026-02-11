"""
Script de validación exhaustiva para `PreciosCalculados`.
- Requiere `pyodbc` y la variable de entorno `SQLSERVER_CONN` (si no, usa cadena por defecto).
- Ejecuta verificaciones de integridad y reglas de negocio: landed vs costo base, markup, precios máximos/mínimos, rangos 0-1, nulos, duplicados.

Uso:
    python Scripts/validate_precios_calculados.py

Salida: imprime un resumen y ejemplos de filas que violan cada regla.
"""
from __future__ import annotations
import os
import sys
from decimal import Decimal
import pyodbc

DEFAULT_CONN = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=.\\SQLEXPRESS;"
    "DATABASE=BD_Calculo_Costos;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

CONN = os.getenv('SQLSERVER_CONN', DEFAULT_CONN)

# Tolerancia para comparaciones monetarias (MXN). Ajusta según precisión deseada.
TOLERANCE = 0.5  # pesos

CHECKS = [
    {
        'id': 'nulls_in_prices',
        'desc': 'Registros con NULL en campos de precio importantes',
        'sql': """
            SELECT TOP 20 sku, transporte, precio_base_mxn, precio_maximo, precio_vendedor_min,
                precio_gerente_com_min, precio_subdireccion_min, precio_direccion_min
            FROM dbo.PreciosCalculados
            WHERE precio_base_mxn IS NULL OR precio_maximo IS NULL OR precio_vendedor_min IS NULL
               OR precio_gerente_com_min IS NULL OR precio_subdireccion_min IS NULL OR precio_direccion_min IS NULL
            ORDER BY fecha_calculo DESC
        """,
    },
    {
        'id': 'negative_values',
        'desc': 'Valores negativos en costos o precios',
        'sql': """
            SELECT TOP 20 sku, transporte, costo_base_mxn, landed_cost_mxn, precio_base_mxn, precio_maximo
            FROM dbo.PreciosCalculados
            WHERE costo_base_mxn < 0 OR landed_cost_mxn < 0 OR precio_base_mxn < 0 OR precio_maximo < 0
            ORDER BY fecha_calculo DESC
        """,
    },
    {
        'id': 'landed_vs_costo',
        'desc': 'Landed cost debe ser >= costo_base_mxn (para importado puede incluir cargos)',
        'sql': """
            SELECT TOP 20 sku, transporte, costo_base_mxn, landed_cost_mxn
            FROM dbo.PreciosCalculados
            WHERE landed_cost_mxn + ? < costo_base_mxn
            ORDER BY fecha_calculo DESC
        """,
        'params': [TOLERANCE]
    },
    {
        'id': 'precio_base_markup_consistency',
        'desc': 'precio_base_mxn ≈ landed_cost_mxn * (1 + markup_pct)',
        'sql': """
            SELECT TOP 20 sku, transporte, landed_cost_mxn, precio_base_mxn, markup_pct,
                ABS(precio_base_mxn - (landed_cost_mxn * (1.0 + COALESCE(markup_pct,0)))) AS diff
            FROM dbo.PreciosCalculados
            WHERE ABS(precio_base_mxn - (landed_cost_mxn * (1.0 + COALESCE(markup_pct,0)))) > ?
            ORDER BY diff DESC
        """,
        'params': [TOLERANCE]
    },
    {
        'id': 'precio_maximo_formula',
        'desc': 'precio_maximo ≈ precio_base_mxn * 2',
        'sql': """
            SELECT TOP 20 sku, transporte, precio_base_mxn, precio_maximo,
                ABS(precio_maximo - (precio_base_mxn * 2.0)) AS diff
            FROM dbo.PreciosCalculados
            WHERE ABS(precio_maximo - (precio_base_mxn * 2.0)) > ?
            ORDER BY diff DESC
        """,
        'params': [TOLERANCE]
    },
    {
        'id': 'discount_ratios',
        'desc': 'Verificar porcentajes esperados: Vendedor 80%, GerCom 75%, Subdir 70%, Direc 65% del precio_maximo',
        'sql': """
            SELECT TOP 50 sku, transporte, precio_maximo,
                precio_vendedor_min, ROUND(100.0 * precio_vendedor_min / NULLIF(precio_maximo,0),2) AS pct_vend,
                precio_gerente_com_min, ROUND(100.0 * precio_gerente_com_min / NULLIF(precio_maximo,0),2) AS pct_gercom,
                precio_subdireccion_min, ROUND(100.0 * precio_subdireccion_min / NULLIF(precio_maximo,0),2) AS pct_sub,
                precio_direccion_min, ROUND(100.0 * precio_direccion_min / NULLIF(precio_maximo,0),2) AS pct_dir
            FROM dbo.PreciosCalculados
            WHERE
                ABS((precio_vendedor_min / NULLIF(precio_maximo,1)) - 0.80) > 0.01
                OR ABS((precio_gerente_com_min / NULLIF(precio_maximo,1)) - 0.75) > 0.01
                OR ABS((precio_subdireccion_min / NULLIF(precio_maximo,1)) - 0.70) > 0.01
                OR ABS((precio_direccion_min / NULLIF(precio_maximo,1)) - 0.65) > 0.01
            ORDER BY fecha_calculo DESC
        """,
    },
    {
        'id': 'markup_pct_ranges',
        'desc': 'Markup_pct debe ser razonable (ej: entre 0.01 y 1.0)',
        'sql': """
            SELECT TOP 50 sku, transporte, markup_pct
            FROM dbo.PreciosCalculados
            WHERE markup_pct IS NULL OR markup_pct < 0.0 OR markup_pct > 5.0
            ORDER BY fecha_calculo DESC
        """,
    },
    {
        'id': 'rate_fields_range',
        'desc': 'Porcentajes (flete, seguro, arancel, dta, honorarios) deben estar en [0,1]',
        'sql': """
            SELECT TOP 50 sku, transporte, flete_pct, seguro_pct, arancel_pct, dta_pct, honorarios_aduanales_pct
            FROM dbo.PreciosCalculados
            WHERE flete_pct < 0 OR flete_pct > 1
               OR seguro_pct < 0 OR seguro_pct > 1
               OR arancel_pct < 0 OR arancel_pct > 1
               OR dta_pct < 0 OR dta_pct > 1
               OR honorarios_aduanales_pct < 0 OR honorarios_aduanales_pct > 1
            ORDER BY fecha_calculo DESC
        """,
    },
    {
        'id': 'duplicates',
        'desc': 'Duplicados por sku+transporte (debería existir UQ)',
        'sql': """
            SELECT sku, transporte, COUNT(*) AS cnt
            FROM dbo.PreciosCalculados
            GROUP BY sku, transporte
            HAVING COUNT(*) > 1
        """,
    },
]


def run():
    try:
        conn = pyodbc.connect(CONN)
    except Exception as e:
        print('ERROR: no fue posible conectar a la base de datos:', e)
        sys.exit(2)

    cursor = conn.cursor()
    total_issues = 0
    print('\nVALIDACIÓN DE `PreciosCalculados` - Informe')
    print('Conexión:', CONN if 'SQLEXPRESS' in CONN else '[env SQLSERVER_CONN]')
    print('-' * 60)

    for check in CHECKS:
        sql = check['sql']
        params = check.get('params', [])
        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            count = len(rows)
        except Exception as e:
            print(f"ERROR ejecutando check {check['id']}: {e}")
            rows = []
            count = -1

        status = 'OK' if count == 0 else f'ISSUES: {count}'
        print(f"[{check['id']}] {check['desc']} -> {status}")
        if count > 0:
            total_issues += count
            # print ejemplos
            max_examples = 5
            for r in rows[:max_examples]:
                print('  -', tuple(r))
        print('-' * 60)

    print(f"Resumen: issues detectados (ejemplos mostrados arriba): {total_issues}")
    conn.close()


if __name__ == '__main__':
    run()
