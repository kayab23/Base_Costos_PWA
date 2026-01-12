# Base Costos PWA Pilot

Sistema de cálculo de Landed Cost y pricing para importaciones, con interfaz PWA para consultas en tiempo real.

## Arquitectura

```
Excel (Plantilla_Pricing_Costos_Importacion.xlsx)
    │
    ├─ sync_excel.py           → Sincroniza catálogo y parámetros
    ├─ cost_engine.py          → Calcula LandedCostCache
    └─ app/ (FastAPI)          → API REST con autenticación
            ↑
frontend/ PWA (fetch + Basic Auth) ↔ /catalog, /pricing, /health
```

Componentes:
- **SQL Server Express** con base `BD_Calculo_Costos` (5 tablas principales)
- **Motor de sincronización** `sync_excel.py` importa desde Excel
- **Motor de cálculo** `cost_engine.py` genera landed costs con nueva fórmula
- **Backend FastAPI** en `app/` con autenticación básica
- **Frontend PWA** en `frontend/` con Service Worker para offline


## Requisitos

1. **Python 3.11+** con entorno virtual
2. **ODBC Driver 18** para SQL Server
3. **SQL Server Express** con base `BD_Calculo_Costos`
4. Dependencias: `pip install -r requirements.txt`

## Estructura de Base de Datos

**Tablas principales:**
- `Productos` (427 SKUs): catálogo con costos base
- `ParametrosImportacion` (7 parámetros): Maritimo, Aereo, Arancel, Seguro, DTA, Honorarios_Aduanales, Mark_up
- `TiposCambio` (4 monedas): tipos de cambio a MXN
- `LandedCostCache` (854 registros): resultados de cálculos
- `Usuarios`: autenticación con bcrypt

**Tablas eliminadas (limpieza 2026-01-08):**
- ~~Versiones~~ - Sistema de versionamiento removido
- ~~PoliticasMargen~~ - Vacía, sin uso
- ~~ControlVersiones~~ - Vacía, sin uso

## Fórmula de Cálculo (Actualizada 2026-01-12)

**Landed Cost para productos importados:**
```
Landed Cost = Costo_Base_MXN × (1 + Flete% + Seguro% + Arancel% + DTA% + Honorarios_Aduanales%)
```

**Mark-up (10% sobre Landed Cost):**
```
Mark-up = Landed Cost × 1.10
```

**Parámetros actuales:**
- Flete Marítimo: 30%
- Flete Aéreo: 120%
- Seguro: 0.6%
- Arancel: 5%
- DTA: 0.8%
- Honorarios Aduanales: 0.45%
- Mark-up: 10%

## Uso Rápido

**1. Sincronizar Excel:**
```bash
python sync_excel.py
```

**2. Calcular Landed Costs:**
```bash
python cost_engine.py --transporte Maritimo
python cost_engine.py --transporte Aereo
```

**3. Iniciar Backend:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**4. Iniciar Frontend:**
```bash
cd frontend
python -m http.server 5173
```

**5. Crear Usuario:**
```bash
python manage_users.py create --username admin --password Admin123! --rol admin
```

## API Endpoints

- `GET /health` - Estado del servidor
- `GET /catalog/productos` - Catálogo completo (requiere auth)
- `GET /pricing/landed?sku={sku}&transporte={transporte}` - Consultar landed cost
- `POST /pricing/recalculate` - Recalcular todos los costos

## Frontend PWA

**Características:**
- Consulta de landed costs en tiempo real
- Filtro por SKU y tipo de transporte
- Exportación a Excel (CSV con UTF-8 BOM)
- Visualización de 10 columnas: SKU, Transporte, Costo Base, Flete%, Seguro%, Arancel%, DTA%, Hon. Aduanales%, Landed Cost, Mark-up
- Service Worker para funcionamiento offline
- Autenticación Basic Auth

**Acceso:**
1. Abrir http://localhost:5173
2. Ingresar credenciales
3. Buscar SKUs y consultar costos
4. Descargar resultados a Excel

## Cambios Recientes (2026-01-12)

### Base de Datos
- ✅ Agregadas columnas `dta_pct` y `honorarios_aduanales_pct` a LandedCostCache
- ✅ Eliminado concepto de `gastos_aduana_fijo` (obsoleto)

### Motor de Cálculo
- ✅ Corregida fórmula: eliminada suma de gastos fijos
- ✅ Nueva fórmula alineada 100% con Excel
- ✅ Recalculados 854 registros (427 Marítimo + 427 Aéreo)

### API y Schemas
- ✅ Agregados campos `dta_pct` y `honorarios_aduanales_pct` a LandedCost schema
- ✅ Actualizada query SQL en pricing.py
- ✅ Eliminado campo `gastos_aduana_mxn` de exportación

### Frontend
- ✅ Tabla expandida de 5 a 10 columnas
- ✅ Agregada función `formatPercentage()` para mostrar porcentajes
- ✅ Exportación Excel actualizada con 14 columnas
- ✅ Valores mostrados coinciden exactamente con Excel

## Git y Control de Versiones

**Commits principales:**
- `0381f2d` - Fix: Eliminar referencias a version_id
- `4cab3ec` - Database cleanup: Eliminadas tablas obsoletas
- `4c62331` - Excel template added
- `51dd852` - Excel export feature

**Archivos ignorados (.gitignore):**
- `.venv/`, `Lib/`, `Scripts/` - Entorno virtual
- `__pycache__/` - Cachés de Python
- `check_*.py`, `fix_*.py`, `test_*.py`, `verify_*.py` - Scripts temporales
- `~$*.xlsx` - Archivos temporales de Excel

## Notas Técnicas

- Backend usa autenticación Basic Auth (migrar a JWT para producción)
- Frontend almacena credenciales en localStorage (considerar sessionStorage)
- Valores en base de datos: porcentajes como decimales (0.30 = 30%)
- Excel: fórmulas con XLOOKUP requieren Excel 2019+
- Python warning "Could not find platform independent libraries" es no-crítico

## Próximos Pasos

1. ~~Sincronizar nuevos parámetros desde Excel~~ ✅
2. ~~Actualizar lógica de cálculo~~ ✅
3. ~~Validar resultados vs Excel~~ ✅
4. Agregar tests automatizados
5. Implementar JWT para autenticación
6. Dockerizar aplicación
7. CI/CD con GitHub Actions
