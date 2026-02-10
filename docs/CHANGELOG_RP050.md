Registro de cambios - RP050

Fecha: 2026-02-10

Resumen:
- Actualicé `Productos` para el SKU `RP050`:
  - `descripcion` => "Base rodable para monitores Biolight P Series"
  - `proveedor` => `TPX`
  - `modelo` => "Soporte para monitores Biolight P Series"
  - `costo_base` => 98 (moneda `USD`)

Cambios en scripts:
- `Scripts/update_product.py`: corregido para comprobar la existencia de la columna `costo_base` antes de ejecutar `ALTER TABLE`, evitando rollbacks que deshacían actualizaciones.
- `Scripts/set_model_rp050.py`: script temporal usado para fijar `modelo` y luego eliminado del repositorio.

Acciones realizadas:
1. Ejecuté `Scripts/update_product.py` para aplicar los cambios iniciales.
2. Se detectó que un `ALTER TABLE` fallido podía provocar rollback; corregí `Scripts/update_product.py` para validar la columna antes de crearla.
3. Fijé manualmente `modelo` para RP050 (temporalmente con `Scripts/set_model_rp050.py`) y verifiqué que ahora aparece en `dbo.Productos`.
4. Recalcule las tablas `dbo.LandedCostCache` y `dbo.PreciosCalculados` para `Maritimo` y `Aereo` (ambas escribieron 428 filas) y verifiqué las entradas para `RP050`.
5. Eliminé `Scripts/set_model_rp050.py` (temporal) del repositorio.
6. Rellené los porcentajes (flete, seguro, arancel, dta, honorarios) en la fila `PreciosCalculados` con `transporte = (SIN_TRANSPORTE)` para `RP050`, de modo que la fila base tenga valores coherentes si se utiliza directamente.

Verificación:
- Ejecuté `Scripts/query_sku_specific.py RP050` y confirmé que `Productos.modelo` ahora contiene "Soporte para monitores Biolight P Series" y que las tablas de costos/precios reflejan los valores recalculados.

Notas:
- Recomendación: revisar manualmente el Excel exportado con modelos inferidos antes de aplicar cambios masivos de `modelo`.
