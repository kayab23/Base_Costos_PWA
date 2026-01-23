# AVANCES IMPLEMENTADOS - SISTEMA DE PRECIOS

## 2026-01-19 - Limpieza y Corrección PDF Multi-SKU
- Eliminado archivo y referencias a `sync_excel.py` (sincronización por Excel obsoleta).
- Limpieza de eventos duplicados y código muerto en frontend (PDF cotización).
- Corrección: ahora proveedor y origen aparecen siempre en el PDF multi-SKU.
- Validación de tipos y normalización de SKUs en frontend.
- Documentación y archivos .md actualizados para reflejar el nuevo flujo y la limpieza.
- **Bug 422 y PDF sin proveedor/origen: CERRADO.**

## 1. Lógica de Jerarquía y Roles
- Implementación de jerarquía de usuarios: Admin, Dirección, Subdirección, Gerencia Comercial, Vendedor.
- Cada rol tiene permisos y vistas diferenciadas, reflejadas en la base de datos y en la interfaz.
- Flujo de autorización escalonado: Vendedor → Gerencia Comercial → Subdirección → Dirección.

## 2. Cálculo de Precios y Descuentos
- Cálculo automático de precios mínimos por rol, basado en porcentaje de descuento sobre el precio máximo.
- Ejemplo de cálculo y reglas documentadas en JERARQUIA_USUARIOS.md.
- Los campos de precios calculados se almacenan en la tabla PreciosCalculados.

## 3. Frontend y Experiencia de Usuario
- Edición libre del campo “Monto Propuesto” para vendedores, con validación de rango y persistencia.
- Actualización dinámica del total negociado solo si hay monto propuesto.
- Separación de vistas y permisos en frontend según el rol.
- PDF multi-SKU con todos los detalles de producto.

## 4. Pruebas y Automatización
- Scripts de pruebas automáticas y monitoreo de cambios (auto_test_login.py, test_login_usuarios.py).
- Pruebas unitarias y de integración en carpeta tests/.
- Scripts de despliegue y backup automatizados (deploy.ps1).

## 5. Buenas Prácticas y Organización
- Código modular y organizado por funcionalidad (app/, frontend/, tests/, sql/).
- Comentarios y docstrings en funciones clave.
- Uso de logs y prints informativos para trazabilidad.
- Eliminados archivos temporales, duplicados y código muerto.

---

**Siguiente paso:**
- Mantener documentación y checklist actualizados tras cada cambio relevante.
- Avanzar en automatización de pruebas y CI/CD.

## 2026-01-23 - Mejoras de generación de PDF y auditoría
- Reorganización completa del layout del PDF de cotización: banda de encabezado fija, logo en esquina superior derecha, título alineado a la izquierda y tabla que usa el ancho utilizable.
- Encabezados abreviados para evitar recortes: `P. Lista`, `Monto Prop.`, `IVA 16%`, `Desc. %`.
- Alineación y formato: valores numéricos centrados bajo sus encabezados; SKU centrado en su celda; renglón de total alineado a la izquierda.
- Inclusión de `M/N` en el monto en letras (moneda nacional) y ajuste de tamaño de fuentes para mejorar legibilidad.
- Implementación de control de saltos de página para evitar que los detalles o totales se corten entre páginas.
- Añadidos endpoints y persistencia: numeración automática de cotizaciones por cliente/vendedor, almacenamiento en tabla `dbo.cotizaciones` y nuevo endpoint `/api/cotizaciones` para auditoría.
- Endpoints de autocompletado para cliente y vendedor (`/api/clientes`, `/api/vendedores`) y cambios menores en el frontend para consumirlos.
- Scripts de prueba usados para validar: `Scripts/request_pdf_api.py`, `Scripts/export_table_png.py` (archivos temporales generados y posteriormente eliminados).

**Notas:** Los archivos temporales de prueba (`api_test_cotizacion.pdf`, `api_test_cotizacion_table_preview.png`) fueron limpiados del repositorio.
