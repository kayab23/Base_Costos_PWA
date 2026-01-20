# Logging de Auditoría para Autorizaciones

## ¿Por qué es importante?
Registrar todas las acciones de autorización permite:
- Auditar quién aprueba, rechaza o solicita descuentos.
- Detectar intentos de acceso no autorizado.
- Cumplir requisitos legales y de control interno.

## ¿Cómo está implementado?
- Todas las acciones clave en el módulo de autorizaciones ([app/routes/autorizaciones.py](app/routes/autorizaciones.py)) usan el logger central (`logger.info`, `logger.warning`, `logger.error`).
- El logger está configurado en [app/logger.py](app/logger.py) para guardar logs rotativos en `logs/app.log`.
- Los logs incluyen usuario, rol, acción, SKU, precio y comentarios relevantes.

## Ejemplo de registro
```
2026-01-19 12:34:56 - INFO - Solicitud creada: usuario=juan sku=ABC123 precio=1000 nivel_autorizador=Gerencia_Comercial
2026-01-19 12:35:10 - INFO - Solicitud aprobada: usuario=gerente id=42 comentario="Autorizado por política especial"
2026-01-19 12:36:00 - ERROR - Intento de solicitud no autorizado: usuario=juan rol=Vendedor
```

## ¿Cómo consultar los logs?
- Revisa el archivo `logs/app.log` en el servidor.
- Puedes filtrar por fechas, usuario, acción, etc.

## Recomendaciones
- No borres los logs salvo por rotación automática.
- Haz backup periódico de los archivos de log.
- Revisa los logs ante cualquier incidente o auditoría.

---
**Referencia:**
- https://docs.python.org/3/library/logging.html
- https://fastapi.tiangolo.com/advanced/logging/
