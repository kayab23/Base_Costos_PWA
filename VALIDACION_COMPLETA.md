## Validación de Jerarquía - HP30B-CTO-01

### ✅ TRANSPORTE AÉREO
| Rol | Usuario | Descuento | Precio Mínimo | Validado |
|-----|---------|-----------|---------------|----------|
| Admin | admin | N/A | Ve todos | ✅ |
| Dirección | direccion1 | 35% | $14,562.38 | ✅ |
| Subdirección | subdir1 | 30% | $15,682.56 | ✅ |
| Gerencia Comercial | gercom1 | 25% | $16,802.75 | ✅ |
| Vendedor | vendedor1 | 20% | $17,922.93 | ✅ |

**Precio Máximo:** $22,403.66

### ✅ TRANSPORTE MARÍTIMO
| Rol | Usuario | Descuento | Precio Mínimo | Validado |
|-----|---------|-----------|---------------|----------|
| Admin | admin | N/A | Ve todos | ✅ |
| Dirección | direccion1 | 35% | $13,939.25 | ✅ |
| Subdirección | subdir1 | 30% | $15,011.50 | ✅ |
| Gerencia Comercial | gercom1 | 25% | $16,083.75 | ✅ |
| Vendedor | vendedor1 | 20% | $17,156.00 | ✅ |

**Precio Máximo:** $21,445.00

### COSTOS DETALLADOS (Visible para todos EXCEPTO Vendedor)

#### Aéreo
- Costo Base: $8,715.00
- Flete: 10.00%
- Seguro: 0.60%
- Arancel: 5.00%
- DTA: 0.80%
- Hon. Aduanales: 0.45%
- Landed Cost: $10,183.48
- Mark-up Base: $11,201.83

#### Marítimo
- Costo Base: $8,715.00
- Flete: 5.00%
- Seguro: 0.60%
- Arancel: 5.00%
- DTA: 0.80%
- Hon. Aduanales: 0.45%
- Landed Cost: $9,747.73
- Mark-up Base: $10,722.50

### PERMISOS DE VISUALIZACIÓN

#### Vendedor
- ❌ NO ve columnas de costos
- ✅ Ve Precio Máximo
- ✅ Ve su Precio Mínimo (20% desc)

#### Gerencia Comercial
- ✅ Ve TODAS las columnas de costos
- ✅ Ve Precio Máximo
- ✅ Ve su Precio Mínimo (25% desc)

#### Subdirección
- ✅ Ve TODAS las columnas de costos
- ✅ Ve Precio Máximo
- ✅ Ve su Precio Mínimo (30% desc)

#### Dirección
- ✅ Ve TODAS las columnas de costos
- ✅ Ve Precio Máximo
- ✅ Ve su Precio Mínimo (35% desc)

#### Admin
- ✅ Ve TODAS las columnas de costos
- ✅ Ve TODOS los precios mínimos

### CONTRASEÑAS ACTUALIZADAS
| Usuario | Contraseña | Estado |
|---------|------------|--------|
| admin | Admin123! | ✅ |
| direccion1 | Direcc123! | ✅ |
| subdir1 | Subdir123! | ✅ |
| gercom1 | GerCom123! | ✅ |
| vendedor1 | Vend123! | ✅ |

### BASE DE DATOS
✅ Tabla `Usuarios` contiene 6 usuarios (incluye gerencia1)
✅ Tabla `PreciosCalculados` tiene los 5 campos de precios mínimos
✅ Todos los cálculos verificados para HP30B-CTO-01

### BACKEND
✅ API `/pricing/listas` retorna todos los campos correctamente
✅ Autenticación Basic Auth funcional
✅ Esquemas Pydantic incluyen todos los campos

### FRONTEND
⚠️ PENDIENTE: Verificar que Gerencia_Comercial vea columnas de costos
- Archivo: `frontend/app.js`
- Línea 398: Actualizada para incluir Gerencia_Comercial en roles que ven costos
