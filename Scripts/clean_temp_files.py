"""
Elimina carpetas __pycache__ y archivos .pyc fuera de .venv, Lib y archive.
Uso: & .venv\Scripts\python.exe Scripts\clean_temp_files.py
"""
from __future__ import annotations
import os
import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE = ['.venv', 'Lib', 'archive']
removed_dirs = []
removed_files = []

for dirpath, dirnames, filenames in os.walk(ROOT):
    # skip excludes
    if any(part in EXCLUDE for part in Path(dirpath).parts):
        continue
    # remove __pycache__ dirs
    if '__pycache__' in dirnames:
        p = Path(dirpath) / '__pycache__'
        try:
            for f in p.rglob('*'):
                f.unlink()
            p.rmdir()
            removed_dirs.append(str(p))
        except Exception:
            pass
    # remove .pyc files
    for f in list(fnmatch.filter(filenames, '*.pyc')):
        fp = Path(dirpath) / f
        try:
            fp.unlink()
            removed_files.append(str(fp))
        except Exception:
            pass

print('Removed dirs:', len(removed_dirs))
for d in removed_dirs:
    print(' -', d)
print('Removed files:', len(removed_files))
for f in removed_files[:200]:
    print(' -', f)
