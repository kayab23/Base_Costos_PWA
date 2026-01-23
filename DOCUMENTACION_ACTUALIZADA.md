# Documentación de Proyecto: Base_Costos (Actualización al 19/01/2026)

## 1. Esquema de Base de Datos (BD_Calculo_Costos)

Tablas principales:
- **Usuarios**: Gestión de usuarios y roles.
- **TiposCambio**: Tipos de cambio históricos y actuales.
- **ListasPrecios**: Precios calculados por SKU y tipo de cliente.
- **PreciosCalculados**: Precios mínimos, máximos y márgenes por SKU.
- **SolicitudesAutorizacion**: Flujo de autorizaciones jerárquicas de descuentos.
- **Productos**: Catálogo principal de productos, incluye columna `costo_base`, `proveedor`, `origen`, `fecha_actualizacion`.
- **ParametrosImportacion**: Parámetros de importación y costos asociados.
- **LandedCostCache**: Cálculo de landed cost por SKU y transporte.

Tablas eliminadas/no usadas: Versiones, CostosBase, PoliticasMargen, ControlVersiones, sync_excel.py.

## 2. Backend y Conexión
- Conexión centralizada en `app/db.py` y `app/config.py` usando `pyodbc` y la variable de entorno `SQLSERVER_CONN`.
- Toda la lógica de negocio, autenticación y cálculo opera sobre la base de datos SQL Server.
- El endpoint `/health` valida la conexión y estado de la base.

## 3. Carga y Actualización de Datos
- **Actualización de productos y costos base:**
  - Se realiza directamente sobre la tabla `Productos`.
  - Ejemplo de actualización masiva:
    ```sql
    UPDATE dbo.Productos SET costo_base = costo_base / 2, fecha_actualizacion = CAST(GETDATE() AS DATE) WHERE sku IN (...);
    ```
- **No se utiliza plantilla Excel ni scripts de sincronización.**

## 4. Flujo de Cotización PDF Multi-SKU
- El frontend arma el payload con todos los SKUs cotizados y sus detalles (incluyendo proveedor y origen).
- El backend valida y genera el PDF correctamente.
- Se corrigió bug de campos faltantes y se eliminó código duplicado.

## 5. Monitoreo, Pruebas y Deployment
- Endpoint `/health` y pruebas automáticas (`pytest`, `playwright`).
- Script `deploy.ps1` para automatizar pruebas, backup, migraciones y reinicio de servicios.
- Documentación de contingencia y checklist en `PLAN_PRODUCCION.md`, `CHECKLIST_PREPRODUCCION.md` y `QUICK_START_PRODUCCION.md`.

## 6. Limpieza y Buenas Prácticas (2026-01-19)
- Eliminado sync_excel.py y referencias a sincronización por Excel.
- Limpieza de eventos duplicados y código muerto en frontend.
- Documentación y archivos .md actualizados.

---

## 7. Cambios recientes (2026-01-23)

- Revisión y mejora del generador de PDFs de cotización:
  - Encabezado con logo en esquina superior derecha y título alineado a la izquierda.
  - Tabla adaptativa al ancho de página, encabezados abreviados y valores alineados.
  - Control de saltos de página y protección del bloque de totales y detalles.
- Auditoría de cotizaciones: persistencia en `dbo.cotizaciones` con `fecha_cotizacion`, `numero_cliente` y `numero_vendedor`.
- Nuevos endpoints para autocompletar clientes y vendedores, y endpoint `/api/cotizaciones` para listar cotizaciones.
- Scripts de prueba usados y luego limpiados del control de versiones cuando eran temporales.

**Última actualización:** 23/01/2026
