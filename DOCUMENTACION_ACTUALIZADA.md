# Documentación de Proyecto: Base_Costos (Actualización al 14/01/2026)

## 1. Esquema de Base de Datos (BD_Calculo_Costos)

Tablas principales:
- **Usuarios**: Gestión de usuarios y roles.
- **TiposCambio**: Tipos de cambio históricos y actuales.
- **ListasPrecios**: Precios calculados por SKU y tipo de cliente.
- **PreciosCalculados**: Precios mínimos, máximos y márgenes por SKU.
- **SolicitudesAutorizacion**: Flujo de autorizaciones jerárquicas de descuentos.
- **Productos**: Catálogo principal de productos, incluye columna `costo_base` y `fecha_actualizacion`.
- **ParametrosImportacion**: Parámetros de importación y costos asociados.
- **LandedCostCache**: Cálculo de landed cost por SKU y transporte.

Tablas eliminadas/no usadas: Versiones, CostosBase, PoliticasMargen, ControlVersiones.

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

## 4. Flujo de Autorizaciones
- Solicitudes gestionadas en la tabla `SolicitudesAutorizacion`.
- Roles: Vendedor, Gerencia_Comercial, Subdireccion, Direccion, admin.
- Lógica jerárquica validada y corregida para todos los niveles.

## 5. Monitoreo, Pruebas y Deployment
- Endpoint `/health` y pruebas automáticas (`pytest`, `playwright`).
- Script `deploy.ps1` para automatizar pruebas, backup, migraciones y reinicio de servicios.
- Documentación de contingencia y checklist en `PLAN_PRODUCCION.md`, `CHECKLIST_PREPRODUCCION.md` y `QUICK_START_PRODUCCION.md`.

## 6. Estado y Operación Actual
- El modelo, backend y scripts están alineados con el uso real y la estructura de la base.
- Todas las actualizaciones de productos y precios se hacen directamente en SQL Server.
- El sistema está listo para operación, monitoreo y futuras mejoras.

---

**Última actualización:** 14/01/2026
