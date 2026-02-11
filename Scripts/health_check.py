import urllib.request
import json
import pyodbc

print('=== PYTHON ENV ===')
import sys
print('python:', sys.executable)

print('\n=== GIT INFO (from environment) ===')
# git info will be printed from shell commands

print('\n=== PYODBC DRIVERS ===')
try:
    print(pyodbc.drivers())
except Exception as e:
    print('pyodbc import error:', e)

print('\n=== HEALTH CHECK (http://127.0.0.1:8000/health) ===')
try:
    with urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5) as r:
        body = r.read().decode(errors='ignore')
        print('status:', r.status)
        print('body:', body)
except Exception as e:
    print('health check error:', str(e))
