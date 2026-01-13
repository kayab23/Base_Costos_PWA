# Jerarquía de Usuarios - Sistema de Precios

## Niveles Jerárquicos (De Mayor a Menor Autoridad)

### 1. Admin
- **Usuario:** `admin`
- **Contraseña:** `Admin123!`
- **Rol en BD:** `admin`
- **Permisos:** Ve todos los costos, todos los niveles de precios
- **Vista:** Todas las columnas de costos + todos los precios mínimos

### 2. Dirección
- **Usuario:** `direccion1`
- **Contraseña:** `Direcc123!`
- **Rol en BD:** `Direccion`
- **Descuento:** 35% sobre Precio Máximo
- **Precio Mínimo (Aéreo):** $14,562.38
- **Precio Mínimo (Marítimo):** $13,939.25
- **Permisos:** Ve todos los costos, puede autorizar hasta su nivel
- **Vista:** Todas las columnas de costos + precio máximo + precio mínimo dirección

### 3. Subdirección
- **Usuario:** `subdir1`
- **Contraseña:** `Subdir123!`
- **Rol en BD:** `Subdireccion`
- **Descuento:** 30% sobre Precio Máximo
- **Precio Mínimo (Aéreo):** $15,682.56
- **Precio Mínimo (Marítimo):** $15,011.50
- **Permisos:** Ve todos los costos, puede solicitar autorización a Dirección
- **Vista:** Todas las columnas de costos + precio máximo + precio mínimo subdirección

### 4. Gerencia Comercial
- **Usuario:** `gercom1`
- **Contraseña:** `GerCom123!`
- **Rol en BD:** `Gerencia_Comercial`
- **Descuento:** 25% sobre Precio Máximo
- **Precio Mínimo (Aéreo):** $16,802.74
- **Precio Mínimo (Marítimo):** $16,083.75
- **Permisos:** Ve todos los costos, puede solicitar autorización a Subdirección
- **Vista:** Todas las columnas de costos + precio máximo + precio mínimo gerencia comercial

### 5. Vendedor
- **Usuario:** `vendedor1`
- **Contraseña:** `Vend123!`
- **Rol en BD:** `Vendedor`
- **Descuento:** 20% sobre Precio Máximo
- **Precio Mínimo (Aéreo):** $17,922.93
- **Precio Mínimo (Marítimo):** $17,156.00
- **Permisos:** NO ve columnas de costos, puede solicitar autorización a Gerencia Comercial
- **Vista:** Solo precio máximo + precio mínimo vendedor (sin columnas de costos)

## Ejemplo de Cálculo para HP30B-CTO-01 Aéreo

- **Precio Base (Mark-up):** $11,201.83
- **Precio Máximo (Base × 2):** $22,403.66

### Descuentos desde Precio Máximo:
1. **Vendedor (20%):** $22,403.66 × 0.80 = $17,922.93
2. **Gerencia Comercial (25%):** $22,403.66 × 0.75 = $16,802.74
3. **Subdirección (30%):** $22,403.66 × 0.70 = $15,682.56
4. **Dirección (35%):** $22,403.66 × 0.65 = $14,562.38

## Flujo de Autorización

```
Vendedor → Gerencia Comercial → Subdirección → Dirección
(20%)         (25%)                 (30%)         (35%)
```

Cada nivel puede:
- Aprobar/rechazar solicitudes del nivel inferior
- Solicitar autorización al nivel superior
- Ver su precio mínimo y todos los superiores

## Campos en Base de Datos (tabla PreciosCalculados)

```sql
precio_maximo              -- Precio base × 2
precio_vendedor_min        -- precio_maximo × 0.80
precio_gerente_com_min     -- precio_maximo × 0.75
precio_subdireccion_min    -- precio_maximo × 0.70
precio_direccion_min       -- precio_maximo × 0.65
```

## Columnas de Costos (visibles según rol)

- **Costo Base MXN**
- **Flete %** (10% Aéreo, 5% Marítimo)
- **Seguro %** (0.60%)
- **Arancel %** (5.00%)
- **DTA %** (0.80%)
- **Hon. Aduanales %** (0.45%)
- **Landed Cost** (costo con todos los impuestos)
- **Mark-up Base** (landed cost × 1.10)

**Visible para:** Admin, Dirección, Subdirección, Gerencia Comercial
**Oculto para:** Vendedor
