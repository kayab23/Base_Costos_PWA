# Dashboard Metrics — Resumen y propósito

Este documento resume cada métrica presentada en el panel de vendedores, qué mide y por qué es importante.

- Total Ventas
  - Qué mide: Suma del valor monetario de las cotizaciones (o ventas registradas) en el periodo seleccionado.
  - Por qué medirla: Proporciona la magnitud del volumen comercial generado en el periodo; útil para seguimiento de objetivos, estacionalidad y tendencias.

- Promedio Valor (Average Quote Value)
  - Qué mide: Valor promedio por cotización (total ventas / número de cotizaciones).
  - Por qué medirla: Ayuda a conocer el tamaño típico de las oportunidades; cambios pueden indicar variaciones en mix de productos, segmentos de clientes o estrategia de precios.

- Win Rate
  - Qué mide: Porcentaje de cotizaciones que se convierten en ventas (ganadas) respecto al total de cotizaciones.
  - Por qué medirla: Mide la efectividad comercial y la calidad de las ofertas; una caída puede indicar problemas en competencia de precio, propuesta de valor o procesos comerciales.

- Avg Margin (Margen Promedio)
  - Qué mide: Margen promedio por operación (%), calculado sobre costo y precio de lista o negociado.
  - Por qué medirla: Mide rentabilidad; permite detectar impactos por descuentos, cambios de costo o políticas de margen.

- Sales By Day (Gráfica de ventas por día)
  - Qué mide: Distribución temporal del ingreso por día dentro del periodo.
  - Por qué medirla: Detectar picos, validación de campañas, ritmo de cierre y ventanas de mayor actividad.

- Top Clients
  - Qué mide: Lista de clientes con mayor contribución al total de ventas en el periodo.
  - Por qué medirla: Identificar concentraciones de riesgo, oportunidades de upsell y priorizar atención comercial.

- Cotizaciones Recientes
  - Qué muestra: Listado de las últimas cotizaciones con enlaces al PDF y valores.
  - Por qué medirla: Permite seguimiento operativo y revisión rápida de casos recientes.

## Recomendaciones de uso
- Revisar `Total Ventas` y `Avg Margin` semanalmente para mantener salud comercial y financiera.
- Monitorizar `Win Rate` y `Promedio Valor` para detectar cambios en calidad de oportunidad o competencia.
- Utilizar `Top Clients` para priorizar recursos comerciales y diseñar estrategias de fidelización.

## Notas técnicas
- Las métricas usan datos almacenados en `dbo.cotizaciones` y `payload_json` para detalles de items.
- Asegurar que los procesos que insertan cotizaciones persisten `monto`, `valor`, y `estado` para cálculos correctos.
