# Script de deployment para producción/desarrollo
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('development','staging','production')]
    [string]$Environment
)

Write-Host "🚀 Iniciando deployment para ambiente: $Environment" -ForegroundColor Green


# 1. Verificar dependencias usando el entorno virtual
Write-Host "`n1️⃣ Verificando dependencias (.venv)..." -ForegroundColor Cyan
& .venv\Scripts\python.exe -m pip list | Select-String "fastapi|uvicorn|pyodbc|bcrypt|openpyxl"

# 2. Ejecutar tests usando el entorno virtual
Write-Host "`n2️⃣ Ejecutando tests (.venv)..." -ForegroundColor Cyan
& .venv\Scripts\python.exe -m pytest tests/ -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Tests fallaron. Abortando deployment." -ForegroundColor Red
    exit 1
}

# 3. Backup de base de datos
Write-Host "`n3️⃣ Creando backup de base de datos..." -ForegroundColor Cyan
$backupDate = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "C:\Backups\BD_Calculo_Costos_$backupDate.bak"
sqlcmd -S localhost\SQLEXPRESS -C -Q "BACKUP DATABASE BD_Calculo_Costos TO DISK = '$backupFile' WITH FORMAT, COMPRESSION"

# 4. Actualizar código desde Git
Write-Host "`n4️⃣ Actualizando código desde Git..." -ForegroundColor Cyan
git pull origin develop

# 5. Aplicar migraciones de BD si existen
Write-Host "`n5️⃣ Aplicando migraciones..." -ForegroundColor Cyan
# Ejecutar scripts SQL en sql/migrations/ si existen

# 6. Reiniciar servicios
Write-Host "`n6️⃣ Reiniciando servicios..." -ForegroundColor Cyan
docker-compose down
docker-compose up -d --build

Write-Host "`n✅ Deployment completado exitosamente!" -ForegroundColor Green
Write-Host "Verificar en: http://localhost:8000/health" -ForegroundColor Yellow
