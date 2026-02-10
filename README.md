# Base Costos PWA Pilot

Sistema de cálculo de Landed Cost y pricing para importaciones, con interfaz PWA para consultas en tiempo real.

## Arquitectura

```
SQL Server Express (BD_Calculo_Costos)
    │
    ├─ cost_engine.py          → Calcula LandedCostCache
    └─ app/ (FastAPI)          → API REST con autenticación
            ↑
frontend/ PWA (fetch + JWT Auth) ↔ /catalog, /pricing, /health, /cotizacion/pdf
```

Componentes:
- **SQL Server Express** con base `BD_Calculo_Costos` (5 tablas principales)
- **Motor de cálculo** `cost_engine.py` genera landed costs con nueva fórmula
- **Backend FastAPI** en `app/` con autenticación JWT
- **Frontend PWA** en `frontend/` con Service Worker para offline

> **Nota:** La sincronización por Excel y el script `sync_excel.py` han sido eliminados. Toda la gestión de productos y costos es directa en la base de datos.

## Requisitos

1. **Python 3.11+** con entorno virtual
2. **ODBC Driver 18** para SQL Server
3. **SQL Server Express** con base `BD_Calculo_Costos`
4. Dependencias: `pip install -r requirements.txt`

## Estructura de Base de Datos

**Tablas principales:**
- `Productos`: catálogo con costos base, proveedor, origen, etc.
- `ParametrosImportacion`: parámetros de importación
- `TiposCambio`: tipos de cambio a MXN
- `LandedCostCache`: resultados de cálculos
- `Usuarios`: autenticación con bcrypt

**Tablas eliminadas (limpieza 2026-01-19):**
- ~~Versiones~~, ~~PoliticasMargen~~, ~~ControlVersiones~~, ~~CostosBase~~, ~~sync_excel.py~~

## Flujo de Cotización PDF Multi-SKU (2026-01-19)
- El frontend permite cotizar múltiples SKUs y genera un PDF con todos los detalles (incluyendo proveedor y origen).
- El backend valida y procesa el payload, generando el PDF correctamente.
- Se eliminó código duplicado y eventos innecesarios, corrigiendo errores 422.

## Cambios Recientes (2026-01-19)
- Eliminado sync_excel.py y referencias a sincronización por Excel.
- Limpieza de eventos duplicados en frontend.
- Corrección de bug: ahora proveedor y origen aparecen siempre en el PDF.
- Documentación y checklist actualizados.

## Política de Descuentos y Flujo de Autorización (2026-01-22)

- Para controlar riesgos comerciales, el sistema aplica límites de descuento según el rol del usuario. Si el `MONTO TOTAL PROPUESTO` excede el porcentaje permitido para el rol, el frontend mostrará una advertencia y bloqueará la generación del PDF hasta que se solicite y obtenga autorización.
- Roles y límites (ejemplo): `vendedor`: 5%, `supervisor`: 15%, `admin`: 100% (sin límite). Estos valores pueden cambiar en la configuración del backend.
- La validación se aplica tanto en frontend (UX) como en backend (`POST /cotizacion/pdf`) — el backend devuelve `403` y un mensaje cuando la solicitud excede el permiso del usuario.

## Cómo ejecutar tests y validar localmente

1. Crear/activar entorno virtual con Python 3.11+ y luego instalar dependencias:

```bash
C:/Users/FernandoOlveraRendon/Documents/Base_Costos/.venv/Scripts/python.exe -m pip install -r requirements.txt
```

2. Iniciar backend (ejemplo):

```bash
C:/Users/FernandoOlveraRendon/Documents/Base_Costos/.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

3. Iniciar servidor estático para frontend:

```bash
cd frontend
python -m http.server 5173
```

4. Ejecutar tests unitarios:

```bash
C:/Users/FernandoOlveraRendon/Documents/Base_Costos/.venv/Scripts/python.exe -m pytest -q
```

5. Ejecutar E2E Playwright (si está instalado y configurado):

```bash
pytest -q tests/test_e2e_discount.py
```

6. Validar generación de PDFs (script de validación incluido):

```bash
C:/Users/FernandoOlveraRendon/Documents/Base_Costos/.venv/Scripts/python.exe scripts/validate_pdf.py
```

### Limpieza de artefactos de prueba

Se añadió el script `tools/cleanup_repo.ps1` para eliminar archivos temporales y respuestas de pruebas generadas localmente. Ejecuta desde la raíz del repo:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\cleanup_repo.ps1
```

El script elimina archivos conocidos de salida de pruebas y `__pycache__` y no borra la carpeta `.venv` ni el código fuente. Revisa la salida antes de hacer commit.

## Uso Rápido

**1. Calcular Landed Costs:**
```bash
python cost_engine.py --transporte Maritimo
python cost_engine.py --transporte Aereo
```

**2. Iniciar Backend:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**3. Iniciar Frontend:**
```bash
cd frontend
python -m http.server 5173
```

**4. Crear Usuario:**
```bash
python manage_users.py create --username admin --password Admin123! --rol admin
```

## API Endpoints

- `GET /health` - Estado del servidor
- `GET /catalog/productos` - Catálogo completo (requiere auth)
- `GET /pricing/landed?sku={sku}&transporte={transporte}` - Consultar landed cost
- `POST /cotizacion/pdf` - Generar PDF de cotización multi-SKU

## Frontend PWA

**Características:**
- Consulta de landed costs en tiempo real
- Cotización y PDF multi-SKU con todos los detalles
- Exportación a Excel (CSV con UTF-8 BOM)
- Visualización de 10 columnas: SKU, Transporte, Costo Base, Flete%, Seguro%, Arancel%, DTA%, Hon. Aduanales%, Landed Cost, Mark-up
- Service Worker para funcionamiento offline
- Autenticación JWT

**Acceso:**
1. Abrir http://localhost:5173
2. Ingresar credenciales
3. Buscar SKUs y consultar costos
4. Descargar resultados a Excel o PDF

## Notas Técnicas

- Backend usa autenticación JWT
- Frontend almacena credenciales en localStorage (considerar sessionStorage)
- Valores en base de datos: porcentajes como decimales (0.30 = 30%)
- Python warning "Could not find platform independent libraries" es no-crítico

## Próximos Pasos

1. Agregar tests automatizados
2. Implementar 2FA para roles críticos
3. Dockerizar aplicación
4. CI/CD con GitHub Actions

---

## Cambios Recientes: Dashboard de Vendedores (2026-01-26)

- Se integró un panel de métricas para vendedores en la interfaz (`frontend/index.html`).
- Se añadió soporte de datos demo (`loadDemoMetrics`) y tooltips responsivos para tarjetas.
- Se corrigieron errores de front-end (JS) y se añadieron validaciones y manejo de errores en `apiFetch()`.
- Ver detalle en `docs/DASHBOARD_CHANGELOG.md`.

## Exportar SKUs a Excel (script nuevo)

- Script: `Scripts/export_sku_prices.py`
- Propósito: generar un reporte Excel con los SKUs y precios mínimos/máximos para vendedores en ambos transportes (`Maritimo`, `Aereo`).
- Columnas generadas: `sku`, `descripcion`, `modelo`, `costo_base_mxn`, `vendedor_min_maritimo`, `maximo_maritimo`, `vendedor_min_aereo`, `maximo_aereo`.
- Nota sobre `modelo`: el script usa `dbo.Productos.modelo` cuando está disponible; si está vacío intenta inferir `modelo` a partir de la `descripcion` usando una heurística regex (puede requerir revisión manual).
- Uso:

```bash
.venv\Scripts\python.exe Scripts\export_sku_prices.py [salida.xlsx]
```

- Si no se indica `salida.xlsx`, el script crea `outputs/sku_prices_YYYYMMDD_HHMMSS.xlsx`.
- Archivo generado en esta ejecución: `outputs/sku_prices_20260210_095509.xlsx`.

Recomendación: revisar los SKUs cuyo `modelo` fue inferido antes de compartir el Excel con terceros.
