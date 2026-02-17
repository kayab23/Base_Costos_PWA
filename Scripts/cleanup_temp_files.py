"""Eliminar archivos y carpetas temporales comunes generados durante desarrollo.
Acciones:
 - Eliminar carpetas __pycache__ recursivas
 - Eliminar archivos .pyc recursivos
 - Eliminar logs/app.log si existe
 - Vaciar carpeta outputs/ (eliminar archivos dentro)
 - Eliminar archivos temporales de Office que empiecen por '~$'
 - Eliminar test_cotizacion.pdf (archivo de prueba)

Este script es conservador: no elimina scripts fuente ni binarios en `Scripts/`.
"""
import os
import shutil

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
removed = []

# Remove __pycache__ directories
for dirpath, dirnames, filenames in os.walk(root):
    for d in list(dirnames):
        if d == '__pycache__':
            full = os.path.join(dirpath, d)
            try:
                shutil.rmtree(full)
                removed.append(full)
            except Exception as e:
                print('Failed to remove', full, e)

# Remove .pyc files
for dirpath, dirnames, filenames in os.walk(root):
    for f in filenames:
        if f.endswith('.pyc'):
            full = os.path.join(dirpath, f)
            try:
                os.remove(full)
                removed.append(full)
            except Exception as e:
                print('Failed to remove', full, e)

# Remove logs/app.log
logf = os.path.join(root, 'logs', 'app.log')
if os.path.exists(logf):
    try:
        os.remove(logf)
        removed.append(logf)
    except Exception as e:
        print('Failed to remove', logf, e)

# Empty outputs/ directory (remove files only)
outputs_dir = os.path.join(root, 'outputs')
if os.path.isdir(outputs_dir):
    for entry in os.listdir(outputs_dir):
        full = os.path.join(outputs_dir, entry)
        try:
            if os.path.isfile(full) or os.path.islink(full):
                os.remove(full)
                removed.append(full)
            elif os.path.isdir(full):
                shutil.rmtree(full)
                removed.append(full)
        except Exception as e:
            print('Failed to remove', full, e)

# Remove temp office files starting with ~$ at repo root
for f in os.listdir(root):
    if f.startswith('~$'):
        full = os.path.join(root, f)
        try:
            os.remove(full)
            removed.append(full)
        except Exception as e:
            print('Failed to remove', full, e)

# Remove test_cotizacion.pdf if exists
test_pdf = os.path.join(root, 'test_cotizacion.pdf')
if os.path.exists(test_pdf):
    try:
        os.remove(test_pdf)
        removed.append(test_pdf)
    except Exception as e:
        print('Failed to remove', test_pdf, e)

# Print summary
if removed:
    print('Removed:')
    for r in removed:
        print(' -', r)
else:
    print('No temp files removed.')
