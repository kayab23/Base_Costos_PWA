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
