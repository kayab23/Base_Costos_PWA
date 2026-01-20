# Guía rápida: Configuración de HTTPS/SSL con Let's Encrypt y Nginx

## 1. Instalar Nginx
```sh
sudo apt update
sudo apt install nginx
```

## 2. Instalar Certbot (Let's Encrypt)
```sh
sudo apt install certbot python3-certbot-nginx
```

## 3. Solicitar el certificado SSL
```sh
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
```
- Sigue las instrucciones para validar el dominio.
- El certificado se instala en `/etc/letsencrypt/live/tu-dominio.com/`.

## 4. Configuración de Nginx
- Usa el archivo `nginx.conf` generado como base.
- Certbot ajusta la configuración automáticamente.

## 5. Renovación automática
Let's Encrypt expira cada 90 días, pero Certbot instala un cron job para renovar automáticamente:
```sh
sudo certbot renew --dry-run
```

## 6. Verifica el candado en el navegador
- Accede a `https://tu-dominio.com` y confirma que la conexión es segura.

---
**Notas:**
- El dominio debe apuntar al servidor antes de ejecutar Certbot.
- El backend FastAPI debe correr en `127.0.0.1:8000`.
- El bloque de puerto 80 en Nginx fuerza redirección HTTP→HTTPS.
- Puedes consultar logs de Nginx en `/var/log/nginx/`.

---
**Referencia oficial:**
- https://certbot.eff.org/
- https://nginx.org/en/docs/
