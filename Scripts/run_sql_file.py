import sys
from pathlib import Path
import pyodbc
from app.config import settings

def main(sql_path):
    p = Path(sql_path)
    if not p.exists():
        print('File not found:', p)
        return 2
    sql = p.read_text(encoding='utf-8')
    conn = None
    try:
        conn = pyodbc.connect(settings.sqlserver_conn, autocommit=False)
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        print('SQL executed successfully')
        return 0
    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        print('ERROR executing SQL:', str(e))
        return 3
    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: run_sql_file.py <path.sql>')
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
