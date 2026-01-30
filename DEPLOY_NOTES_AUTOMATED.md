Resumen de cambios rápidos para despliegue y pruebas E2E

- Frontend port:
  - `docker-compose.yml`: el mapeo de puerto host para `frontend` fue cambiado a `5174:5173` para evitar el conflicto con herramientas locales que usan `5173`. Si en tu máquina `5173` está libre puedes revertirlo.

- Redis / SSE:
  - `backend` necesita `REDIS_URL` en el entorno para habilitar Pub/Sub y hacer que SSE funcione entre workers (multi-worker).
  - Ejemplo en `docker-compose.yml` ya incluye `REDIS_URL=redis://redis:6379/0`.
  - Verificación rápida ejecutada: suscriptor `curl -N` dentro del contenedor backend y publicación de prueba (`redis-cli PUBLISH autorizaciones_events '{"test":"ping"}'`) recibida correctamente.

- Healthchecks y dependencias:
  - `backend` tiene `healthcheck` que consulta `/health`.
  - Asegúrate de instalar `ODBC Driver` en imágenes de producción si vas a usar `pyodbc` (en build actual usamos `SKIP_ODBC=1` para desarrollo local).

- Logs y seguridad:
  - `LOG_FILE` escrito en `logs/app.log` dentro del contenedor; monta volumen o configura agregador (ELK/Fluentd) en producción.
  - No exponer secrets en `docker-compose.yml`; usa `docker secrets` o un provider (Vault) en producción.

- Pasos recomendados para pruebas E2E reproducibles:
  1. `docker-compose up -d --build redis backend frontend`
  2. Conectar un cliente SSE (desde host o dentro del contenedor). Ejemplo (dentro del contenedor backend):
     - `docker exec -d backend sh -c "curl -N http://127.0.0.1:8000/autorizaciones/events > /tmp/sse_out.txt 2>&1 &"`
  3. Crear solicitud y aprobarla (scripts en `Scripts/`):
     - `test_solicitud_autorizacion_vendedor.ps1`
     - `approve_admin_from_resp.ps1`
  4. Verificar `/tmp/sse_out.txt` dentro del contenedor o `Scripts/sse_output.txt` en host para mensajes `created`/`approved`.

- Notas:
  - Si no ves eventos desde un navegador/host, confirma que `REDIS_URL` está presente y que el cliente SSE se conecta antes de crear/aprobar la solicitud.
  - Para modo single-worker (debug), puedes iniciar el backend con `UVICORN_WORKERS=1` para probar el broadcaster in-memory.

Si quieres, completo la sección de "endurecimiento" con snippets para `docker secrets`, `systemd` unit, y una plantilla `docker-compose.prod.yml`.

## Endurecimiento rápido (snippets)

### Docker secrets (Swarm)

1) Crear secretos en un nodo Swarm:

   ```bash
   echo "supersecreto" | docker secret create SECRET_KEY -
   echo "db_password_here" | docker secret create DB_PASSWORD -
   ```

2) Referenciarlos en `docker-compose.prod.yml` (Swarm mode):

   ```yaml
   secrets:
     SECRET_KEY:
       external: true
     DB_PASSWORD:
       external: true
   ```

3) En el servicio `backend`:

   ```yaml
   services:
     backend:
       image: myorg/base_costos:latest
       secrets:
         - SECRET_KEY
         - DB_PASSWORD
       environment:
         - DATABASE_PASSWORD_FILE=/run/secrets/DB_PASSWORD
   ```

> Nota: Docker secrets requiere Swarm; en hosts individuales usa un `.env` protegido o un proveedor de secretos (Vault).

### Plantilla `docker-compose.prod.yml` (mínima)

```yaml
services:
  redis:
    image: redis:7-alpine
    restart: unless-stopped

  backend:
    image: myorg/base_costos:latest
    env_file: .env.prod
    environment:
      - ENVIRONMENT=production
    ports:
      - "8000:8000"
    depends_on:
      - redis
    restart: always
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "5"

secrets:
  SECRET_KEY:
    external: true
  DB_PASSWORD:
    external: true
```

### `systemd` unit (ejemplo para `/etc/systemd/system/base_costos.service`)

```ini
[Unit]
Description=Base Costos docker-compose
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/srv/base_costos
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d --remove-orphans
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=300
TimeoutStopSec=300

[Install]
WantedBy=multi-user.target
```

Habilitar y arrancar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable base_costos.service
sudo systemctl start base_costos.service
```

### Recomendaciones finales

- Usa un registry privado con tags inmutables y orquestador (Swarm/K8s) para producción.
- No almacenes secretos en repositorios ni en `docker-compose.yml`.
- Centraliza logs y añade monitoreo/alertas para `healthcheck` failures.

Si quieres, genero `docker-compose.prod.yml` y el unit file listos en el repo y los adapto a tu entorno.
