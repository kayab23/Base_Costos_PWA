@echo off
REM Script rápido para deployment local/producción
REM Uso: start_deploy.bat development|staging|production

if "%1"=="" (
    echo Debes indicar el ambiente: development, staging o production
    exit /b 1
)

powershell -ExecutionPolicy Bypass -File deploy.ps1 -Environment %1
