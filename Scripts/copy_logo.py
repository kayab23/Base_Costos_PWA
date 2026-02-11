"""
Small helper to copy frontend logo to backend PDF folder if missing.
Usage:
    python scripts/copy_logo.py [--force]

This script is safe to run locally; it will report actions taken.
"""
import shutil
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, 'frontend', 'icons', 'logo.png')
DST_DIR = os.path.join(ROOT, 'app', 'pdf')
DST = os.path.join(DST_DIR, 'logo.png')

force = '--force' in sys.argv

if not os.path.exists(SRC):
    print(f"Source logo not found: {SRC}")
    sys.exit(2)

if not os.path.isdir(DST_DIR):
    os.makedirs(DST_DIR, exist_ok=True)

if os.path.exists(DST) and not force:
    print(f"Destination already exists: {DST} (use --force to overwrite)")
    sys.exit(0)

try:
    shutil.copy2(SRC, DST)
    print(f"Copied {SRC} -> {DST}")
    sys.exit(0)
except Exception as e:
    print(f"Error copying logo: {e}")
    sys.exit(3)
