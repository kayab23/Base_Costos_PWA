@echo off
REM Script para pruebas locales: backend y frontend

set BACKEND_PORT=8000
set FRONTEND_PORT=5173
set VENV_ACTIVATE=%~dp0.venv\Scripts\activate
set VENV_PYTHON=%~dp0.venv\Scripts\python.exe

echo Iniciando backend en http://127.0.0.1:%BACKEND_PORT%
start "Backend" cmd /k "call %VENV_ACTIVATE% && %VENV_PYTHON% -m uvicorn app.main:app --host 0.0.0.0 --port %BACKEND_PORT% --reload"

echo Iniciando frontend en http://127.0.0.1:%FRONTEND_PORT%
start "Frontend" cmd /k "call %VENV_ACTIVATE% && %VENV_PYTHON% -m http.server %FRONTEND_PORT% --directory frontend"

echo ---------------------------------------------
echo Backend:  http://127.0.0.1:%BACKEND_PORT%
echo Frontend: http://127.0.0.1:%FRONTEND_PORT%
echo ---------------------------------------------
pause
