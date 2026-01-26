Resumen de cambios: Dashboard — tooltips y gráficos

Fecha: 2026-01-26

Cambios realizados:

- Reemplazo del tooltip CSS pseudo-element por un tooltip gestionado por JavaScript.
  - Archivo: `frontend/app.js`
  - Comportamiento: un único `div.metric-tooltip` se inyecta en el `body` y se posiciona dinámicamente encima/abajo del icono `i`. Esto evita desbordes verticales y recortes en tarjetas pequeñas.
- Ajustes de estilo responsive del tooltip.
  - Archivo: `frontend/styles.css`
  - Ahora el tooltip es multilínea, calcula `max-width` relativo a la ventana y se queda dentro de los límites de la pantalla.
- Corrección en `renderCharts` para usar variables CSS antes de su lectura y añadir caídas seguras cuando no hay datos.
  - Archivo: `frontend/app.js`
- Añadido export CSV y sparklines en la tabla `Resumen por Vendedor`.
  - Archivo: `frontend/app.js`
- Añadido script de validación automatizada para `PreciosCalculados`.
  - Archivo: `Scripts/validate_precios_calculados.py`

Recomendaciones inmediatas:

- Ejecutar `Scripts/validate_precios_calculados.py` contra la BD de staging/producción y revisar las filas que el script marque como issues.
- Probar el dashboard en distintos tamaños de pantalla (desktop, tablet, móvil) y comprobar posicionamiento del tooltip y que las gráficas se renderizan.

Comandos útiles:

```bash
# Ejecutar validación de PreciosCalculados
python Scripts/validate_precios_calculados.py

# Forzar recarga del frontend (si usas server local)
# (ejecutar en la carpeta del proyecto)
git status
git pull
# Si desarrollas con servidor estático, reinícialo
```

Contacto / notas:

- Si aparece contenido extremadamente largo (una sola palabra sin espacios) en `data-tooltip`, el navegador puede forzarlo a romper por caracteres; en ese caso recomiendo truncar el texto con "…" y mostrar el contenido completo en un modal o en el CSV de exportación.

Plan de mejora propuesto para mañana (prioridad):

1. Ejecutar el script de validación y listar resultados (bloqueante si hay violaciones severas).
2. Corregir automáticamente (con transacción y revisión) casos triviales: recalcular `precio_base_mxn` y `precio_maximo` donde difieran más de tolerancia.
3. Implementar paginación servidor/cliente para `Resumen por Vendedor` y asegurar rendimiento.
4. Terminar la renderización de sparklines con mini-Plotly/Canvas con hover mínimo.
5. Poblar datalists de `clientes` y `vendedores` mediante endpoints y debounce.
6. Añadir job/CI que ejecute el script de validación en cada `push` a `main` y reporte fallos.

---
