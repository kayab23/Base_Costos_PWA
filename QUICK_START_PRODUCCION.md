# Guía de Inicio Rápido - Preparación para Producción

**Prioridad de implementación:** Fases ordenadas de menor a mayor complejidad

---

## 🚀 **FASE 1: Configuración Básica (1-2 horas)**

### ✅ **Paso 1.1: Crear archivo de variables de entorno**

```bash
# Crear .env en la raíz del proyecto
cd c:\Users\FernandoOlveraRendon\Documents\Base_Costos
```

Crear archivo `.env` con:

```env
# Base de Datos
DATABASE_SERVER=localhost\\SQLEXPRESS
DATABASE_NAME=BD_Calculo_Costos
DATABASE_DRIVER=ODBC Driver 18 for SQL Server

# Seguridad
SECRET_KEY=tu-secret-key-aqui-cambiar-en-produccion
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Modo
ENVIRONMENT=development
```

**Acción inmediata:**
```powershell
# Instalar python-dotenv si no está
pip install python-dotenv
```

### ✅ **Paso 1.2: Actualizar config.py para usar .env**

Modificar `app/config.py` para leer variables de entorno.

### ✅ **Paso 1.3: Actualizar .gitignore**

Asegurar que `.env` NO se suba a Git:
```bash
echo ".env" >> .gitignore
```

---

## 🔐 **FASE 2: Seguridad Básica (2-3 horas)**

### ✅ **Paso 2.1: Implementar logging robusto**

Crear `app/logger.py`:

```python
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Logger principal
    logger = logging.getLogger("cost_app")
    logger.setLevel(logging.INFO)
    
    # Handler para archivo (rotativo)
    file_handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter('%(levelname)s: %(message)s')
    )
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger()
```

**Usar en endpoints:**
```python
from .logger import logger

@router.post("/autorizaciones/solicitar")
def crear_solicitud(...):
    logger.info(f"Usuario {user['username']} solicitó autorización para SKU {data.sku}")
    # ... resto del código
```

### ✅ **Paso 2.2: Agregar logging de auditoría en autorizaciones**

En `app/routes/autorizaciones.py`:
- Log cuando se crea solicitud
- Log cuando se aprueba/rechaza
- Incluir: usuario, timestamp, SKU, precio, resultado

### ✅ **Paso 2.3: Implementar validación de sesión timeout**

En frontend `app.js`, agregar:

```javascript
let lastActivity = Date.now();
const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutos

// Actualizar actividad en cada interacción
document.addEventListener('click', () => lastActivity = Date.now());
document.addEventListener('keypress', () => lastActivity = Date.now());

// Verificar timeout cada minuto
setInterval(() => {
    if (Date.now() - lastActivity > SESSION_TIMEOUT) {
        alert('Sesión expirada por inactividad. Por favor, inicia sesión nuevamente.');
        localStorage.removeItem('authToken');
        window.location.reload();
    }
}, 60000);
```

---

## 💾 **FASE 3: Base de Datos - Optimizaciones (1 hora)**

### ✅ **Paso 3.1: Crear índices para mejorar performance**

Ejecutar en SQL Server:

```sql
USE BD_Calculo_Costos;
GO

-- Índice en Productos.sku (búsquedas frecuentes)
CREATE NONCLUSTERED INDEX IX_Productos_SKU 
ON dbo.Productos(sku);

-- Índice compuesto en PreciosCalculados
CREATE NONCLUSTERED INDEX IX_PreciosCalculados_SKU_Transporte 
ON dbo.PreciosCalculados(sku, transporte);

-- Índice en SolicitudesAutorizacion para filtros por estado
CREATE NONCLUSTERED INDEX IX_SolicitudesAutorizacion_Estado_Solicitante
ON dbo.SolicitudesAutorizacion(estado, solicitante_id);

-- Índice en Usuarios.username (para login)
CREATE NONCLUSTERED INDEX IX_Usuarios_Username
ON dbo.Usuarios(username) WHERE es_activo = 1;

-- Verificar índices creados
SELECT 
    t.name AS Tabla,
    i.name AS Indice,
    i.type_desc AS Tipo
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.name IN ('Productos', 'PreciosCalculados', 'SolicitudesAutorizacion', 'Usuarios')
ORDER BY t.name, i.name;
```

### ✅ **Paso 3.2: Crear script de backup manual**

Crear `sql/backup_database.sql`:

```sql
-- Backup completo de BD
BACKUP DATABASE BD_Calculo_Costos
TO DISK = 'C:\Backups\BD_Calculo_Costos_Manual.bak'
WITH FORMAT,
     NAME = 'Backup Manual Pre-Producción',
     COMPRESSION;

-- Verificar backup
RESTORE VERIFYONLY 
FROM DISK = 'C:\Backups\BD_Calculo_Costos_Manual.bak';
```

**Ejecutar ahora:**
```powershell
# Crear directorio de backups
mkdir C:\Backups -ErrorAction SilentlyContinue

# Ejecutar backup
sqlcmd -S localhost\SQLEXPRESS -d BD_Calculo_Costos -C -i sql/backup_database.sql
```

---

## 🧪 **FASE 4: Testing Básico (2-3 horas)**

### ✅ **Paso 4.1: Crear tests unitarios para cálculos críticos**

Crear `tests/test_cost_engine.py`:

```python
import pytest
from cost_engine import calculate_landed_costs, normalize_number

def test_normalize_number():
    assert normalize_number(100) == 100.0
    assert normalize_number("100.50") == 100.5
    assert normalize_number(None) == 0.0
    assert normalize_number("") == 0.0

def test_landed_cost_aereo():
    """Verifica cálculo de Landed Cost para transporte Aéreo"""
    productos = [{
        "sku": "TEST-001",
        "origen": "Importado",
        "categoria": "Hardware",
        "moneda_base": "USD",
        "costo_base": 100.0
    }]
    
    # TC USD = 20 MXN
    fx_map = {"USD": 20.0, "MXN": 1.0}
    
    # Parámetros: 10% flete aéreo, 2% seguro, 15% arancel, etc.
    pct_params = {
        "seguro": 0.02,
        "arancel": 0.15,
        "dta": 0.01,
        "honorarios_aduanales": 0.005,
        "mark_up": 0.10
    }
    
    result = calculate_landed_costs(
        productos, {}, fx_map, pct_params, {}, "Aereo"
    )
    
    assert len(result) == 1
    assert result[0]["flete_pct"] == 0.10  # 10% para aéreo
    assert result[0]["costo_base_mxn"] == 2000.0  # 100 USD * 20
    # Landed = 2000 * (1 + 0.10 + 0.02 + 0.15 + 0.01 + 0.005)
    assert result[0]["landed_cost_mxn"] == pytest.approx(2570.0, rel=0.01)

def test_landed_cost_maritimo():
    """Verifica cálculo de Landed Cost para transporte Marítimo"""
    # Similar al anterior pero flete_pct debe ser 0.05 (5%)
    pass

def test_precio_vendedor():
    """Verifica que precio vendedor = precio_maximo * 0.80"""
    # Implementar test
    pass
```

**Instalar pytest y ejecutar:**
```powershell
pip install pytest
pytest tests/test_cost_engine.py -v
```

### ✅ **Paso 4.2: Test de endpoints críticos**

Crear `tests/test_api.py`:

```python
from fastapi.testclient import TestClient
from app.main import app
import base64

client = TestClient(app)

def get_auth_header(username, password):
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {credentials}"}

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200

def test_login_vendedor():
    headers = get_auth_header("vendedor1", "Vend123!")
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["rol"] == "Vendedor"

def test_listas_precios_vendedor():
    """Vendedor debe ver solo precio máximo y su mínimo"""
    headers = get_auth_header("vendedor1", "Vend123!")
    response = client.get("/pricing/listas?sku=HP30B-CTO-01", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    # Vendedor NO debe ver costos
    assert "costo_base_mxn" not in data[0] or data[0]["costo_base_mxn"] is None

def test_listas_precios_gerencia():
    """Gerencia debe ver todos los costos"""
    headers = get_auth_header("gercom1", "GerCom123!")
    response = client.get("/pricing/listas?sku=HP30B-CTO-01", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    # Gerencia SÍ debe ver costos
    assert data[0]["costo_base_mxn"] is not None
```

**Ejecutar:**
```powershell
pytest tests/test_api.py -v
```

---

## 📊 **FASE 5: Monitoreo y Métricas (1 hora)**

### ✅ **Paso 5.1: Mejorar endpoint /health con métricas**

En `app/main.py`:

```python
from datetime import datetime, timezone
import psutil  # pip install psutil

start_time = datetime.now(timezone.utc)

@app.get("/health")
def healthcheck():
    uptime_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
    
    # Verificar conexión a BD
    try:
        from .db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        db_status = "OK"
    except Exception as e:
        db_status = f"ERROR: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "OK" else "unhealthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_seconds,
        "database": db_status,
        "memory_percent": psutil.virtual_memory().percent,
        "cpu_percent": psutil.cpu_percent(interval=1)
    }
```

### ✅ **Paso 5.2: Crear dashboard simple de monitoreo**

Crear `frontend/monitor.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Monitor del Sistema</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial; padding: 20px; background: #f5f5f5; }
        .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status-ok { color: green; font-weight: bold; }
        .status-error { color: red; font-weight: bold; }
        .metric { display: flex; justify-content: space-between; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>🖥️ Monitor del Sistema</h1>
    <div id="status" class="card">Cargando...</div>
    
    <script>
        async function checkHealth() {
            try {
                const response = await fetch('http://localhost:8000/health');
                const data = await response.json();
                
                const statusClass = data.status === 'healthy' ? 'status-ok' : 'status-error';
                const uptime = Math.floor(data.uptime_seconds / 60);
                
                document.getElementById('status').innerHTML = `
                    <h2>Estado: <span class="${statusClass}">${data.status.toUpperCase()}</span></h2>
                    <div class="metric"><span>⏱️ Tiempo activo:</span><span>${uptime} minutos</span></div>
                    <div class="metric"><span>💾 Base de datos:</span><span>${data.database}</span></div>
                    <div class="metric"><span>🧠 Memoria:</span><span>${data.memory_percent}%</span></div>
                    <div class="metric"><span>⚙️ CPU:</span><span>${data.cpu_percent}%</span></div>
                    <div class="metric"><span>🕐 Última actualización:</span><span>${new Date(data.timestamp).toLocaleString()}</span></div>
                `;
            } catch (error) {
                document.getElementById('status').innerHTML = `
                    <h2 class="status-error">❌ Error de conexión</h2>
                    <p>${error.message}</p>
                `;
            }
        }
        
        // Actualizar cada 5 segundos
        checkHealth();
        setInterval(checkHealth, 5000);
    </script>
</body>
</html>
```

**Acceso:** http://localhost:5173/monitor.html

---

## 🔧 **FASE 6: Configuración de Producción (1-2 horas)**

### ✅ **Paso 6.1: Crear script de deployment**

Crear `deploy.ps1`:

```powershell
# Script de deployment para producción
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('development','staging','production')]
    [string]$Environment
)

Write-Host "🚀 Iniciando deployment para ambiente: $Environment" -ForegroundColor Green

# 1. Verificar dependencias
Write-Host "`n1️⃣ Verificando dependencias..." -ForegroundColor Cyan
pip list | Select-String "fastapi|uvicorn|pyodbc|bcrypt|openpyxl"

# 2. Ejecutar tests
Write-Host "`n2️⃣ Ejecutando tests..." -ForegroundColor Cyan
pytest tests/ -v
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
git pull origin master

# 5. Aplicar migraciones de BD si existen
Write-Host "`n5️⃣ Aplicando migraciones..." -ForegroundColor Cyan
# Ejecutar scripts SQL en sql/migrations/ si existen

# 6. Reiniciar servicios
Write-Host "`n6️⃣ Reiniciando servicios..." -ForegroundColor Cyan
# Detener backend (ajustar según método de ejecución)
# Iniciar backend con configuración de $Environment

Write-Host "`n✅ Deployment completado exitosamente!" -ForegroundColor Green
Write-Host "📊 Verificar en: http://localhost:8000/health" -ForegroundColor Yellow
```

**Ejecutar:**
```powershell
.\deploy.ps1 -Environment development
```

---

## 📋 **Resumen de Prioridades**

### **🔴 ALTA PRIORIDAD (Hacer AHORA)**
1. ✅ Configurar `.env` y variables de entorno
2. ✅ Implementar logging robusto con archivos rotativos
3. ✅ Crear índices en base de datos
4. ✅ Configurar backup manual de BD
5. ✅ Mejorar endpoint `/health` con métricas

### **🟡 MEDIA PRIORIDAD (Esta semana)**
1. ✅ Escribir tests unitarios básicos
2. ✅ Implementar timeout de sesión en frontend
3. ✅ Crear script de deployment
4. ⚠️ Migrar contraseñas a formato más seguro (12+ caracteres)
5. ⚠️ Documentar procedimientos de backup/restore

### **🟢 BAJA PRIORIDAD (Próximas 2 semanas)**
1. ⚠️ Implementar JWT en lugar de HTTP Basic Auth
2. ⚠️ Configurar rate limiting
3. ⚠️ Implementar caché Redis
4. ⚠️ Configurar CI/CD pipeline
5. ⚠️ Preparar ambiente de staging

---

## 🎯 **Siguiente Paso Inmediato**

**Ejecuta estos comandos AHORA:**

```powershell
# 1. Crear directorios necesarios
cd c:\Users\FernandoOlveraRendon\Documents\Base_Costos
mkdir logs, tests, C:\Backups -ErrorAction SilentlyContinue

# 2. Instalar dependencias adicionales
pip install python-dotenv pytest psutil

# 3. Crear archivo .env (editar manualmente después)
@"
DATABASE_SERVER=localhost\SQLEXPRESS
DATABASE_NAME=BD_Calculo_Costos
DATABASE_DRIVER=ODBC Driver 18 for SQL Server
SECRET_KEY=cambiar-en-produccion-usar-secreto-seguro
ENVIRONMENT=development
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
"@ | Out-File .env -Encoding utf8

# 4. Crear backup inmediato
sqlcmd -S localhost\SQLEXPRESS -C -Q "BACKUP DATABASE BD_Calculo_Costos TO DISK = 'C:\Backups\BD_Pre_Produccion.bak' WITH FORMAT, COMPRESSION"

# 5. Verificar que todo funciona
python -c "from dotenv import load_dotenv; load_dotenv(); print('✅ .env cargado correctamente')"
```

**¿Quieres que implemente alguna de estas fases en particular?**
