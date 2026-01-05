# Base Costos PWA Pilot

Documenta el pipeline completo del piloto para calcular landed cost y publicar precios desde SQL Server, exponerlos mediante FastAPI y consultarlos con una PWA ligera.

## Arquitectura en 60 segundos

```
Excel (Plantilla_Pricing_Costos_Importacion.xlsx)
    │
    ├─ sync_excel.py           → Llena tablas base y crea una versión
    ├─ cost_engine.py          → Calcula LandedCostCache + ListaPrecios
    └─ app/ (FastAPI)          → Expone catálogos, cálculos y recálculo
            ↑
frontend/ PWA (fetch + Basic Auth) ↔ /catalog, /pricing, /health
```

Componentes físicos:
- **SQL Server Express** con la base `BD_Calculo_Costos`. El esquema completo está en `sql/schema.sql` y el parche incremental para usuarios en `sql/add_usuarios_table.sql`.
- **Motor de sincronización** `sync_excel.py` que limpia tablas operativas y reimporta desde la plantilla Excel (requieres `openpyxl`).
- **Motor de cálculo** `cost_engine.py` que genera y persiste landed cost y precios (invocado manualmente o vía `/pricing/recalculate`).
- **Backend FastAPI** bajo `app/` con autenticación básica y rutas para catálogos/pricing.
- **Herramientas auxiliares** (`manage_users.py`, `inspect_workbook.py`) para crear usuarios y explorar hojas Excel.
- **Frontend PWA** en `frontend/` que actúa como consola de operador y cachea recursos vía Service Worker.

## Requisitos previos

1. **Python 3.11+** con acceso al archivo `requirements.txt`. Usa entorno virtual: `py -3.11 -m venv .venv` y actívalo antes de instalar dependencias.
2. **ODBC Driver 18** para SQL Server y conectividad local a `localhost` o `.\\SQLEXPRESS`.
3. **SQL Server Express** (o equivalente) con una base en blanco y permisos para crear tablas, vistas y usuarios.
4. **Node.js / npm** (opcional) para servir la PWA o usa `python -m http.server 5173` desde `frontend/`.
5. **Git 2.52+** ya instalado (ruta `C:\Program Files\Git\cmd`). Si la terminal no lo reconoce, abrir una nueva sesión tras ejecutar `setx PATH` como hicimos hoy.

Variables relevantes:
- `SQLSERVER_CONN`: cadena completa de conexión. Si no está definida, `cost_engine.py`, `app/config.py` y `manage_users.py` usan `DRIVER={ODBC Driver 18 for SQL Server};SERVER=.\SQLEXPRESS;DATABASE=BD_Calculo_Costos;Trusted_Connection=yes;TrustServerCertificate=yes;`.

## Inicialización de datos

1. Ejecuta `sql/schema.sql` en `BD_Calculo_Costos` para crear todas las tablas (Versiones, Productos, CostosBase, ParametrosImportacion, TiposCambio, PoliticasMargen, LandedCostCache, ListaPrecios, ControlVersiones, Usuarios).
2. (Opcional) Si el esquema ya existe pero falta la tabla de usuarios, aplica `sql/add_usuarios_table.sql`.
3. Coloca/actualiza la plantilla `Plantilla_Pricing_Costos_Importacion.xlsx` en la raíz del proyecto.
4. Corre `python sync_excel.py` (usa `SQLSERVER_CONN` si necesitas otra instancia). El script:
   - Registra una nueva fila en `Versiones`.
   - Limpia tablas operativas con `DELETE`.
   - Inserta catálogos, costos, parámetros, tipos de cambio, márgenes y control de versiones.

## Motor de cálculo (`cost_engine.py`)

- Implementa utilidades para normalizar números, construir mapas de costos/FX y separar parámetros fijos vs porcentuales.
- Calcula landed cost según origen, transporte y parámetros de importación, aplicando seguros, fletes, aranceles y gastos fijos.
- Construye listas de precio por tipo de cliente y monedas destino, imponiendo `PRICE_MIN_MULTIPLIER = 1.10` como piso.
- Persiste resultados limpiando `dbo.LandedCostCache` y `dbo.ListaPrecios` antes de insertar nuevos registros.
- CLI: `python cost_engine.py --transporte Maritimo --moneda-precio MXN --moneda-precio USD`.

## Backend FastAPI (`app/`)

- `app/main.py`: crea la instancia, configura CORS (orígenes `http://localhost:5173` y `http://127.0.0.1:5173`) y publica `/health`.
- `app/config.py`: centraliza settings (cadena SQL, transporte y monedas por defecto, metadatos de API).
- `app/db.py`: helpers para conexiones y selección de filas.
- `app/security.py`: hashing/verificación bcrypt con parche para passlib + bcrypt 4.
- `app/auth.py`: dependencia `get_current_user()` que valida credenciales HTTP Basic contra `dbo.Usuarios`.
- `app/routes/catalog.py`: endpoints `/catalog/*` para productos, costos, parámetros, tipos de cambio y márgenes (todos protegidos).
- `app/routes/pricing.py`: entrega landed cost y lista de precios, además de `POST /pricing/recalculate` que invoca `run_calculations()` reutilizando la conexión abierta.
- `app/schemas.py`: modelos Pydantic para respuestas/solicitudes.

### Ejecución local

```bash
(.venv) uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Con Basic Auth, crea al menos un usuario:

```bash
(.venv) python manage_users.py create --username admin --password Admin123! --rol admin
```

> **Nota temporal**: las contraseñas se almacenan con bcrypt pero el transporte no es TLS. En escenarios reales usa HTTPS y un proveedor de identidad más robusto.

## Frontend PWA (`frontend/`)

- `index.html`: landing con tarjeta de autenticación, tablas para productos y landed cost, y formulario para recalcular.
- `app.js`: maneja estado en `localStorage`, construye cabecera Basic Auth y consume `/health`, `/catalog/productos`, `/pricing/landed`, `/pricing/recalculate`. Limita la renderización a 25 filas para mantener el layout.
- `styles.css`: diseño tipo "glass" con la fuente Space Grotesk y soporte responsivo.
- `sw.js` + `manifest.webmanifest`: Service Worker cache-first y metadatos PWA (icons en `frontend/icons/`).

Servir en local:

```bash
# opción 1
(.venv) python -m http.server 5173 --directory frontend
# opción 2
npx serve frontend
```

Luego abre `http://localhost:5173`, ingresa la URL del backend (`http://localhost:8000` por defecto) y credenciales creadas con `manage_users.py`.

## Herramientas auxiliares

- `inspect_workbook.py`: imprime dimensiones, encabezados, muestras de filas y fórmulas por hoja para depurar inconsistencias en la plantilla Excel.
- Carpeta `Lib/site-packages`: entorno autónomo con dependencias (openpyxl, pyodbc, etc.) preinstaladas para ejecutar scripts aunque no se active `.venv`. Mantenerla sincronizada si actualizas dependencias.
- `Scripts/`: binarios del entorno virtual (Windows) utilizados por `python`, `pip`, `uvicorn`, etc.

## Flujo operativo recomendado

1. **Sincronizar Excel → SQL** con `python sync_excel.py` cuando recibas una nueva versión de la plantilla.
2. **Ejecutar cálculos** (manual o via `POST /pricing/recalculate`).
3. **Validar catálogos/costeo** usando `/catalog/*` y `/pricing/*` desde la PWA o herramientas externas.
4. **Compartir resultados** exportando desde `dbo.ListaPrecios` o mostrando la PWA en tablets/desktop.

## Elementos temporales y pendientes

- PWA usa Basic Auth almacenado en `localStorage`. Migrar a tokens cortos o OAuth cuando se exponga públicamente.
- Los íconos bajo `frontend/icons/` son placeholders documentados en `frontend/icons/README.txt`; reemplazarlos antes de empaquetar.
- El motor elimina completamente las tablas `LandedCostCache` y `ListaPrecios` antes de insertar; si se requiere histórico debe añadir versionamiento.
- No existen pruebas automatizadas; ejecutar `sync_excel.py` y `cost_engine.py` manualmente después de cada cambio mayor.
- Git se instaló hoy pero la terminal actual no refresca PATH automáticamente; abrir un shell nuevo antes de correr `git --version`.

## Próximos pasos sugeridos

1. Inicializar el repositorio Git local (`git init`, `.gitignore` para `.venv/`, `Lib/`, etc.).
2. Crear commits documentando sincronización/calculadora/PWA y empujar a `https://github.com/kayab23/Base_Costos_PWA.git`.
3. Definir pipeline de despliegue (por ejemplo, contenedor con FastAPI + reverse proxy y hosting estático para la PWA).
4. Extender documentación con diagramas y ejemplos de API (FastAPI genera `/docs` automáticamente una vez en ejecución).
