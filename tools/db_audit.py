"""
DB audit (solo lectura). Imprime JSON con:
- tablas
- columnas
- primary keys
- foreign keys
- índices
- row counts (desde sys.dm_db_partition_stats)
- detección de columnas de "última modificación" y un MAX(...) si existe

Uso: python tools/db_audit.py

No realiza cambios en la BD.
"""
import json
import sys
import traceback
from pathlib import Path

try:
    from app.config import settings
except Exception:
    # try importing as module when executed from repo root
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from app.config import settings

try:
    import pyodbc
except Exception:
    print(json.dumps({"error": "pyodbc no está instalado en el entorno. Instala pyodbc en el virtualenv."}))
    sys.exit(1)

def fetchall_dict(cursor):
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

def main():
    out = {"tables": []}
    conn_str = settings.sqlserver_conn
    try:
        conn = pyodbc.connect(conn_str, autocommit=True)
    except Exception as e:
        print(json.dumps({"error": "No se pudo conectar a la BD", "details": str(e)}))
        return

    cur = conn.cursor()

    # List tables
    cur.execute("SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' ORDER BY TABLE_SCHEMA, TABLE_NAME")
    tables = cur.fetchall()

    for schema, table in tables:
        tbl = {"schema": schema, "name": table}
        # columns
        cur.execute("SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=? AND TABLE_NAME=? ORDER BY ORDINAL_POSITION", (schema, table))
        tbl["columns"] = fetchall_dict(cur)

        # primary keys
        cur.execute(
            """
            SELECT kcu.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
              ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
            WHERE tc.TABLE_SCHEMA = ? AND tc.TABLE_NAME = ? AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
            ORDER BY kcu.ORDINAL_POSITION
            """,
            (schema, table)
        )
        pk = [r[0] for r in cur.fetchall()]
        tbl["primary_key"] = pk

        # foreign keys
        cur.execute(
            """
            SELECT
              fk.CONSTRAINT_NAME,
              kcu.COLUMN_NAME,
              pk.TABLE_SCHEMA AS referenced_schema,
              pk.TABLE_NAME AS referenced_table,
              rcu.COLUMN_NAME AS referenced_column
            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS fk
            JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE ccu ON fk.CONSTRAINT_NAME = ccu.CONSTRAINT_NAME
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu ON fk.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE rcu ON fk.UNIQUE_CONSTRAINT_NAME = rcu.CONSTRAINT_NAME
            JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS pk ON fk.UNIQUE_CONSTRAINT_NAME = pk.CONSTRAINT_NAME
            WHERE kcu.TABLE_SCHEMA = ? AND kcu.TABLE_NAME = ?
            """,
            (schema, table)
        )
        fk_rows = fetchall_dict(cur)
        tbl["foreign_keys"] = fk_rows

        # indexes
        cur.execute(
            """
            SELECT i.name AS index_name, i.is_unique, i.is_primary_key, ic.key_ordinal, col.name AS column_name
            FROM sys.indexes i
            JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            JOIN sys.columns col ON ic.object_id = col.object_id AND ic.column_id = col.column_id
            JOIN sys.tables t ON i.object_id = t.object_id
            JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE s.name = ? AND t.name = ?
            ORDER BY i.name, ic.key_ordinal
            """,
            (schema, table)
        )
        tbl["indexes"] = fetchall_dict(cur)

        # row counts via sys.partitions (sum of rows for index 0/1)
        try:
            cur.execute(
                """
                SELECT SUM(p.rows) AS rows
                FROM sys.partitions p
                JOIN sys.tables t ON p.object_id = t.object_id
                JOIN sys.schemas s ON t.schema_id = s.schema_id
                WHERE s.name = ? AND t.name = ? AND p.index_id IN (0,1)
                GROUP BY t.name
                """,
                (schema, table)
            )
            r = cur.fetchone()
            tbl["row_count"] = r[0] if r else 0
        except Exception:
            tbl["row_count"] = None

        # detect common "last modified" columns and compute MAX(col)
        candidate_cols = [c.get("COLUMN_NAME") for c in tbl["columns"] if isinstance(c, dict)]
        last_cols = [c for c in candidate_cols if c.lower() in ("fecha_actualizacion","updated_at","modified_at","updated_at","last_modified","created_at","fecha","fecha_modificacion")] 
        tbl["detected_last_modified_columns"] = last_cols
        tbl["last_modified_samples"] = {}
        for col in last_cols:
            try:
                q = f"SELECT MAX([{col}]) as m FROM [{schema}].[{table}]"
                cur.execute(q)
                val = cur.fetchone()
                tbl["last_modified_samples"][col] = str(val[0]) if val and val[0] is not None else None
            except Exception:
                tbl["last_modified_samples"][col] = None

        out["tables"].append(tbl)

    # additionally, list recent objects in sys.objects for creation/modify dates (where available)
    try:
        cur.execute(
            "SELECT s.name as schema_name, o.name as object_name, o.type_desc, o.create_date, o.modify_date FROM sys.objects o JOIN sys.schemas s ON o.schema_id = s.schema_id WHERE o.type IN ('U') ORDER BY o.modify_date DESC"
        )
        out["objects"] = fetchall_dict(cur)
    except Exception:
        out["objects"] = []

    print(json.dumps(out, indent=2, default=str, ensure_ascii=False))

if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(2)
