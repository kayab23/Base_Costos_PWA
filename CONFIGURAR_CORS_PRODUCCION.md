# Configuración de CORS para Producción

## ¿Qué es CORS?
CORS (Cross-Origin Resource Sharing) permite controlar qué dominios pueden acceder a tu API desde el navegador. Es clave para evitar ataques y proteger tu backend.

## Configuración recomendada
- En desarrollo, permite orígenes locales:
  ```env
  ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://frontend:5173
  ```
- En producción, solo permite tu dominio real:
  ```env
  ALLOWED_ORIGINS=https://tu-dominio.com
  ```

## ¿Cómo cambiar?
1. Edita el archivo `.env` y actualiza la variable `ALLOWED_ORIGINS` con el dominio autorizado.
2. Reinicia el backend para aplicar los cambios.

## Ejemplo en FastAPI
La configuración en `main.py` ya toma los orígenes desde `.env`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

## Notas
- No es necesario modificar el código para cambiar los orígenes, solo el archivo `.env`.
- Mantén los orígenes locales solo mientras desarrollas.
- En producción, usa solo el dominio público.

---
**Referencia:**
- https://fastapi.tiangolo.com/tutorial/cors/
