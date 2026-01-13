# Plan de Paso a Producción - Sistema de Cálculo de Costos

**Fecha de preparación:** 13 de enero de 2026  
**Estado actual:** Ambiente de desarrollo completado y documentado  
**Objetivo:** Despliegue seguro y controlado a producción

---

## 📋 **Checklist Pre-Producción**

### ✅ **Completado en Desarrollo**

- [x] Arquitectura backend FastAPI funcional
- [x] Frontend PWA responsive completado
- [x] Sistema de autenticación HTTP Basic con bcrypt
- [x] Motor de cálculo de Landed Cost y Precios
- [x] Sistema de autorizaciones jerárquicas (4 niveles)
- [x] Sincronización de datos desde Excel
- [x] Documentación completa del código
- [x] Control de versiones Git configurado
- [x] Archivos temporales eliminados
- [x] 5 usuarios de prueba configurados y validados

### 🔧 **Tareas Pendientes para Producción**

#### **1. Seguridad**
- [ ] Migrar de HTTP Basic Auth a JWT tokens con refresh tokens
- [ ] Implementar rate limiting en endpoints críticos
- [ ] Configurar HTTPS/SSL en servidor web
- [ ] Implementar secrets management (no hardcodear credenciales)
- [ ] Configurar CORS restrictivo (solo dominios autorizados)
- [ ] Agregar logging de auditoría para todas las autorizaciones
- [ ] Implementar 2FA (autenticación de dos factores) para roles admin/dirección

#### **2. Base de Datos**
- [ ] Migrar de SQL Server Express a SQL Server Standard/Enterprise
- [ ] Configurar backups automáticos diarios con retención de 30 días
- [ ] Implementar índices en columnas de búsqueda frecuente:
  - `Productos.sku`
  - `PreciosCalculados.sku, transporte`
  - `SolicitudesAutorizacion.solicitante_id, estado`
- [ ] Configurar usuario de BD con permisos mínimos (no usar sa o admin)
- [ ] Implementar stored procedures para operaciones críticas
- [ ] Crear views para reportes comunes
- [ ] Configurar alertas de espacio en disco

#### **3. Infraestructura**
- [ ] Provisionar servidor dedicado o VPS (mínimo 4GB RAM, 2 vCPUs)
- [ ] Instalar y configurar Nginx como reverse proxy
- [ ] Configurar firewall (solo puertos 80/443 abiertos)
- [ ] Implementar monitoreo de recursos (CPU, RAM, disco)
- [ ] Configurar servicio systemd para auto-restart de uvicorn
- [ ] Configurar backup automático de archivos Excel y código
- [ ] Implementar CDN para assets estáticos del frontend

#### **4. Aplicación**
- [ ] Configurar variables de entorno (.env) para:
  - `DATABASE_CONN_STR`
  - `SECRET_KEY` (para JWT)
  - `ALLOWED_ORIGINS`
  - `LOG_LEVEL`
- [ ] Cambiar `DEBUG=False` en producción
- [ ] Implementar logging robusto (archivo rotativo):
  - Accesos (access.log)
  - Errores (error.log)
  - Autorizaciones (audit.log)
- [ ] Configurar Sentry o similar para tracking de errores
- [ ] Implementar health check endpoint con métricas
- [ ] Optimizar queries N+1 con JOINs
- [ ] Implementar caché Redis para consultas frecuentes

#### **5. Frontend**
- [ ] Minificar y comprimir JS/CSS (webpack/vite build)
- [ ] Configurar service worker para caché offline mejorado
- [ ] Implementar timeout de sesión (auto-logout después de inactividad)
- [ ] Agregar confirmación en acciones críticas (aprobar/rechazar)
- [ ] Implementar mensajes de error amigables (no mostrar stack traces)
- [ ] Configurar Google Analytics o similar para monitoreo de uso

#### **6. Testing**
- [ ] Escribir tests unitarios para funciones críticas:
  - `calculate_landed_costs()`
  - `calculate_price_lists()`
  - `determinar_autorizador()`
- [ ] Tests de integración para endpoints principales
- [ ] Pruebas de carga (Apache Bench o Locust):
  - Mínimo 100 usuarios concurrentes
  - 1000 requests por minuto sostenidos
- [ ] Pruebas de penetración (OWASP Top 10)
- [ ] Validación de permisos por rol (matriz de acceso)

#### **7. Datos**
- [ ] Crear usuarios de producción reales (eliminar usuarios de prueba)
- [ ] Importar catálogo completo de productos
- [ ] Validar todos los parámetros de importación
- [ ] Configurar tipos de cambio actualizados
- [ ] Ejecutar cálculo inicial completo (Aéreo + Marítimo)
- [ ] Validar precios calculados contra precios actuales

#### **8. Documentación**
- [ ] Manual de usuario final (PDF + video)
- [ ] Guía de administración del sistema
- [ ] Procedimientos de backup/restore
- [ ] Plan de recuperación ante desastres
- [ ] Matriz de contactos de soporte
- [ ] Calendario de mantenimiento programado

#### **9. Capacitación**
- [ ] Sesión de entrenamiento para vendedores
- [ ] Sesión de entrenamiento para gerentes comerciales
- [ ] Sesión de entrenamiento para subdirección/dirección
- [ ] Sesión de entrenamiento para administradores TI
- [ ] Crear videos tutoriales por rol
- [ ] Documentar preguntas frecuentes (FAQ)

#### **10. Migración y Despliegue**
- [ ] Plan de rollback en caso de fallas
- [ ] Definir ventana de mantenimiento (fuera de horario laboral)
- [ ] Configurar ambiente de staging (réplica exacta de producción)
- [ ] Ejecutar smoke tests en staging
- [ ] Migrar datos de desarrollo a producción
- [ ] Desplegar backend en servidor de producción
- [ ] Desplegar frontend en servidor web
- [ ] Configurar DNS apuntando al servidor
- [ ] Monitoreo activo durante primeras 48 horas

---

## 📊 **Arquitectura de Producción Recomendada**

```
┌─────────────────────────────────────────────────────────┐
│                      INTERNET                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │   Cloudflare CDN    │ (Opcional - caché global)
          │   + DDoS Protection │
          └──────────┬──────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │  Nginx Reverse Proxy│
          │  Port 80/443 (HTTPS)│
          └──────────┬──────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │
│   (Static PWA)  │    │   FastAPI       │
│   Port 5173     │    │   uvicorn 8000  │
└─────────────────┘    └────────┬────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
         ┌──────────────────┐    ┌──────────────────┐
         │  SQL Server      │    │  Redis Cache     │
         │  (Producción)    │    │  (Opcional)      │
         │  Port 1433       │    │  Port 6379       │
         └──────────────────┘    └──────────────────┘
```

---

## 🔐 **Matriz de Usuarios Producción**

Crear usuarios reales con estructura:

| Username | Rol | Departamento | Email Corporativo |
|----------|-----|--------------|-------------------|
| admin.sistemas | admin | TI | sistemas@empresa.com |
| direccion.ventas | Direccion | Dirección Comercial | director.comercial@empresa.com |
| subdir.ventas | Subdireccion | Subdirección Ventas | subdir.ventas@empresa.com |
| gerente.com1 | Gerencia_Comercial | Gerencia Comercial | gerente1@empresa.com |
| gerente.com2 | Gerencia_Comercial | Gerencia Comercial | gerente2@empresa.com |
| vendedor.juan | Vendedor | Ventas Zona Norte | juan.vendedor@empresa.com |
| vendedor.maria | Vendedor | Ventas Zona Sur | maria.vendedor@empresa.com |

**Políticas de contraseñas producción:**
- Mínimo 12 caracteres
- Al menos 1 mayúscula, 1 minúscula, 1 número, 1 símbolo
- Cambio obligatorio cada 90 días
- No reutilizar últimas 5 contraseñas
- Bloqueo después de 5 intentos fallidos

---

## 📈 **Métricas de Éxito Post-Despliegue**

Monitorear durante primeros 30 días:

- **Disponibilidad:** ≥99.5% uptime
- **Performance:** Tiempo de respuesta API <500ms p95
- **Errores:** Tasa de error <1% de requests
- **Adopción:** ≥80% de vendedores activos en primera semana
- **Autorizaciones:** Tiempo promedio de aprobación <2 horas
- **Satisfacción:** NPS ≥7/10 en encuesta de usuarios

---

## 🚨 **Plan de Contingencia**

### **Escenario 1: Base de datos caída**
1. Verificar servicio SQL Server
2. Intentar restart del servicio
3. Si persiste: Restaurar desde backup más reciente
4. Notificar a usuarios tiempo estimado de recuperación

### **Escenario 2: Backend API no responde**
1. Verificar logs de uvicorn/fastapi
2. Restart del servicio systemd
3. Verificar conectividad con base de datos
4. Si persiste: Rollback a versión anterior estable

### **Escenario 3: Precios calculados incorrectos**
1. Detener cálculos automáticos
2. Analizar logs de cost_engine.py
3. Validar parámetros de importación en BD
4. Ejecutar recálculo manual con parámetros correctos
5. Auditar precios antes de reactivar acceso

### **Escenario 4: Fuga de datos o acceso no autorizado**
1. Bloquear inmediatamente acceso externo (firewall)
2. Revisar logs de acceso y autenticación
3. Resetear contraseñas de todos los usuarios
4. Auditoría de seguridad completa
5. Notificar a dirección y cumplimiento legal

---

## 📝 **Checklist Día del Go-Live**

**T-24 horas:**
- [ ] Backup completo de BD de desarrollo
- [ ] Congelar cambios de código (code freeze)
- [ ] Notificar a usuarios de ventana de mantenimiento

**T-4 horas:**
- [ ] Desplegar a staging y ejecutar smoke tests
- [ ] Verificar configuración de producción
- [ ] Confirmar plan de rollback listo

**T-0 (Hora del deploy):**
- [ ] Apagar servicios de desarrollo
- [ ] Restaurar backup en BD de producción
- [ ] Desplegar backend y frontend
- [ ] Verificar health checks (200 OK)
- [ ] Prueba de login con cada rol
- [ ] Prueba de cálculo de precios (1 SKU)
- [ ] Prueba de flujo completo de autorización

**T+1 hora:**
- [ ] Notificar a usuarios que sistema está disponible
- [ ] Monitoreo activo de logs y métricas
- [ ] Soporte en línea durante primeras 4 horas

**T+24 horas:**
- [ ] Revisión de métricas del primer día
- [ ] Recolección de feedback de usuarios
- [ ] Ajustes menores según necesidad

---

## 🎯 **Criterios de Éxito del Proyecto**

1. **Funcionalidad:** Todos los cálculos de precios son precisos y consistentes
2. **Seguridad:** No se han reportado incidentes de seguridad o accesos no autorizados
3. **Adopción:** ≥90% de usuarios capacitados usan el sistema regularmente
4. **Performance:** Tiempos de respuesta aceptables (<1s para consultas)
5. **Estabilidad:** <2 incidentes críticos por mes después de estabilización
6. **Satisfacción:** Retroalimentación positiva de stakeholders (NPS ≥7)

---

## 📞 **Contactos de Soporte**

| Rol | Nombre | Email | Teléfono | Disponibilidad |
|-----|--------|-------|----------|----------------|
| Líder de Proyecto | [Nombre] | [email] | [tel] | L-V 8am-6pm |
| Desarrollador Backend | [Nombre] | [email] | [tel] | Guardia 24/7 primera semana |
| DBA | [Nombre] | [email] | [tel] | L-V 9am-5pm |
| Soporte TI | [Nombre] | [email] | [tel] | L-V 8am-6pm |
| Director Comercial | [Nombre] | [email] | [tel] | Escalamiento crítico |

---

**Preparado por:** Sistema de Desarrollo  
**Última actualización:** 13 de enero de 2026  
**Versión:** 1.0
