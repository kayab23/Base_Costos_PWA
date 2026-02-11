"""
Detecta y opcionalmente actualiza categorías en `dbo.Productos` a 'equipo'|'insumo'
para SKUs importados (moneda_base != 'MXN') usando una heurística por palabras clave.

Ejecución:
 - Dry-run (por defecto): muestra sugerencias sin aplicar.
 - Para aplicar: setear APPLY=1 en entorno.

Uso:
    & .venv\Scripts\python.exe Scripts\batch_map_categories.py
    $env:APPLY='1'; & .venv\Scripts\python.exe Scripts\batch_map_categories.py
"""
from __future__ import annotations
import os
import pyodbc
import re

DEFAULT_CONN = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=.\\SQLEXPRESS;"
    "DATABASE=BD_Calculo_Costos;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)
CONN = os.getenv('SQLSERVER_CONN', DEFAULT_CONN)

KEYWORDS_EQUIPO = [r'equipo', r'soporte', r'monitor', r'lcd', r'led', r'laptop', r'notebook', r'pc', r'impre(sora|soras)', r'server']
KEYWORDS_INSUMO = [r'insumo', r'consumible', r'cartucho', r'papel', r'repuesto', r'accesorio', r'cable', r'adaptador']

def norm(s: str | None) -> str:
    return (s or '').strip().lower()

def guess_category(categoria: str, descripcion: str) -> str | None:
    txt = (categoria + ' ' + descripcion).lower()
    for kw in KEYWORDS_EQUIPO:
        if re.search(kw, txt):
            return 'equipo'
    for kw in KEYWORDS_INSUMO:
        if re.search(kw, txt):
            return 'insumo'
    return None

def main():
    try:
        conn = pyodbc.connect(CONN)
    except Exception as e:
        print('ERROR conectando a BD:', e)
        return
    cur = conn.cursor()
    # Seleccionar SKUs importados o con moneda != MXN y categoria no normalizada
    cur.execute("SELECT sku, categoria, descripcion, moneda_base FROM dbo.Productos WHERE ISNULL(moneda_base,'MXN') <> 'MXN'")
    rows = cur.fetchall()
    candidates = []
    for r in rows:
        sku, cat, desc, moneda = r[0], r[1] or '', r[2] or '', r[3] or ''
        cat_norm = norm(cat)
        if cat_norm in ('equipo','insumo'):
            continue
        guessed = guess_category(cat or '', desc or '')
        if guessed:
            candidates.append((sku, cat, desc, moneda, guessed))

    print(f'Encontrados {len(candidates)} SKUs candidatos a normalizar (moneda != MXN). Mostrando 20 ejemplos:')
    for c in candidates[:20]:
        print(c)

    if not candidates:
        conn.close()
        return

    if os.getenv('APPLY','') == '1':
        print('\nAplicando cambios...')
        updated = 0
        for sku, cat, desc, moneda, guessed in candidates:
            try:
                cur.execute("UPDATE dbo.Productos SET categoria = ? WHERE sku = ?", (guessed, sku))
                updated += cur.rowcount
            except Exception as e:
                print('ERROR updating', sku, e)
        conn.commit()
        print(f'Actualizaciones aplicadas: {updated}')
    else:
        print('\nDry-run: no se aplicaron cambios. Para aplicar, exporta APPLY=1 en el entorno y reejecuta.')

    conn.close()

if __name__ == '__main__':
    main()
