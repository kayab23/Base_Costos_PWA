# Checklist Pre-Producción

## 1. Variables de entorno (.env)
- DATABASE_SERVER
- DATABASE_NAME
- DATABASE_DRIVER
- SQLSERVER_CONN (si aplica)
- SECRET_KEY
- ALGORITHM
- ACCESS_TOKEN_EXPIRE_MINUTES
- ALLOWED_ORIGINS
- LOG_LEVEL
- LOG_FILE
- ENVIRONMENT

## 2. Puertos a abrir en firewall/router
- 8000 (Backend FastAPI)
- 5173 (Frontend)
- 1433 (SQL Server, solo si se requiere acceso externo)
- 9090 (Prometheus, opcional)
- 3000 (Grafana, opcional)

## 3. Usuarios y contraseñas
- Usuarios de la app (admin, direccion1, subdir1, gercom1, vendedor1)
- Contraseñas seguras y actualizadas
- Usuario y contraseña de SQL Server

## 4. Pasos para restaurar/migrar la base de datos
- Restaurar backup con SQL Server Management Studio o script
- Verificar integridad y acceso a tablas
- Ejecutar scripts de migración si existen (sql/migrations/)

## 5. Validaciones finales
- Ejecutar `pytest tests/ -v` y asegurar que todos los tests pasen
- Verificar logs en logs/app.log
- Probar endpoints críticos: /health, /metrics, /auth, /pricing/listas
- Validar acceso desde frontend y diferentes navegadores
- Verificar monitoreo en Prometheus y Grafana

## 6. Seguridad
- Cambiar todas las contraseñas por defecto
- Configurar HTTPS (Let’s Encrypt) y dominio si aplica
- Limitar acceso a puertos solo a IPs necesarias
- Realizar backup completo antes de pasar a producción

---

**Este checklist debe ser revisado antes de cada despliegue en producción.**
