-- =====================================================
-- VALIDACIÓN COMPLETA DE JERARQUÍA DE USUARIOS
-- Base de Datos: BD_Calculo_Costos
-- =====================================================

-- 1. VERIFICAR TABLA USUARIOS
PRINT '=== TABLA USUARIOS ==='
PRINT ''
SELECT 
    usuario_id AS ID,
    username AS Usuario,
    rol AS Rol_BD,
    es_activo AS Activo,
    CONVERT(VARCHAR(10), creado_en, 120) AS Fecha_Creacion
FROM dbo.Usuarios
ORDER BY 
    CASE rol 
        WHEN 'admin' THEN 1 
        WHEN 'Direccion' THEN 2 
        WHEN 'Subdireccion' THEN 3 
        WHEN 'Gerencia_Comercial' THEN 4 
        WHEN 'Vendedor' THEN 5 
        ELSE 6 
    END;
GO

-- 2. VERIFICAR ESTRUCTURA DE PRECIOSCALCULADOS
PRINT ''
PRINT '=== COLUMNAS DE PRECIOSCALCULADOS ==='
PRINT ''
SELECT 
    COLUMN_NAME AS Columna,
    DATA_TYPE AS Tipo,
    CASE 
        WHEN CHARACTER_MAXIMUM_LENGTH IS NOT NULL 
        THEN CONCAT(DATA_TYPE, '(', CHARACTER_MAXIMUM_LENGTH, ')')
        ELSE DATA_TYPE
    END AS Definicion
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'PreciosCalculados' 
  AND TABLE_SCHEMA = 'dbo'
  AND COLUMN_NAME LIKE 'precio%'
ORDER BY ORDINAL_POSITION;
GO

-- 3. VERIFICAR PRECIOS PARA HP30B-CTO-01
PRINT ''
PRINT '=== PRECIOS HP30B-CTO-01 (Ejemplo de Validación) ==='
PRINT ''
SELECT 
    sku AS SKU,
    transporte AS Transporte,
    CAST(precio_maximo AS DECIMAL(10,2)) AS Precio_Maximo,
    CAST(precio_vendedor_min AS DECIMAL(10,2)) AS Vendedor_Min,
    CAST(precio_gerente_com_min AS DECIMAL(10,2)) AS GerCom_Min,
    CAST(precio_subdireccion_min AS DECIMAL(10,2)) AS Subdir_Min,
    CAST(precio_direccion_min AS DECIMAL(10,2)) AS Direcc_Min
FROM dbo.PreciosCalculados 
WHERE sku = 'HP30B-CTO-01'
ORDER BY transporte;
GO

-- 4. VALIDAR CÁLCULO DE DESCUENTOS (Aéreo)
PRINT ''
PRINT '=== VALIDACIÓN DE DESCUENTOS (HP30B-CTO-01 Aéreo) ==='
PRINT ''
SELECT 
    'Precio Máximo' AS Concepto,
    CAST(precio_maximo AS DECIMAL(10,2)) AS Valor,
    '100%' AS Porcentaje
FROM dbo.PreciosCalculados 
WHERE sku = 'HP30B-CTO-01' AND transporte = 'Aereo'
UNION ALL
SELECT 
    'Vendedor (20% desc)',
    CAST(precio_vendedor_min AS DECIMAL(10,2)),
    CAST((precio_vendedor_min / precio_maximo * 100) AS DECIMAL(5,2)) + '%'
FROM dbo.PreciosCalculados 
WHERE sku = 'HP30B-CTO-01' AND transporte = 'Aereo'
UNION ALL
SELECT 
    'Gerencia Comercial (25% desc)',
    CAST(precio_gerente_com_min AS DECIMAL(10,2)),
    CAST((precio_gerente_com_min / precio_maximo * 100) AS DECIMAL(5,2)) + '%'
FROM dbo.PreciosCalculados 
WHERE sku = 'HP30B-CTO-01' AND transporte = 'Aereo'
UNION ALL
SELECT 
    'Subdirección (30% desc)',
    CAST(precio_subdireccion_min AS DECIMAL(10,2)),
    CAST((precio_subdireccion_min / precio_maximo * 100) AS DECIMAL(5,2)) + '%'
FROM dbo.PreciosCalculados 
WHERE sku = 'HP30B-CTO-01' AND transporte = 'Aereo'
UNION ALL
SELECT 
    'Dirección (35% desc)',
    CAST(precio_direccion_min AS DECIMAL(10,2)),
    CAST((precio_direccion_min / precio_maximo * 100) AS DECIMAL(5,2)) + '%'
FROM dbo.PreciosCalculados 
WHERE sku = 'HP30B-CTO-01' AND transporte = 'Aereo';
GO

-- 5. CONTAR PRODUCTOS CON PRECIOS CALCULADOS
PRINT ''
PRINT '=== RESUMEN DE PRODUCTOS ==='
PRINT ''
SELECT 
    COUNT(DISTINCT sku) AS Total_SKUs,
    COUNT(*) AS Total_Registros,
    SUM(CASE WHEN transporte = 'Aereo' THEN 1 ELSE 0 END) AS Registros_Aereo,
    SUM(CASE WHEN transporte = 'Maritimo' THEN 1 ELSE 0 END) AS Registros_Maritimo
FROM dbo.PreciosCalculados;
GO

-- 6. VERIFICAR QUE NO HAYA NULOS EN PRECIOS
PRINT ''
PRINT '=== VERIFICACIÓN DE INTEGRIDAD ==='
PRINT ''
SELECT 
    COUNT(*) AS Total_Registros,
    SUM(CASE WHEN precio_maximo IS NULL THEN 1 ELSE 0 END) AS Nulos_PrecioMax,
    SUM(CASE WHEN precio_vendedor_min IS NULL THEN 1 ELSE 0 END) AS Nulos_VendMin,
    SUM(CASE WHEN precio_gerente_com_min IS NULL THEN 1 ELSE 0 END) AS Nulos_GerMin,
    SUM(CASE WHEN precio_subdireccion_min IS NULL THEN 1 ELSE 0 END) AS Nulos_SubMin,
    SUM(CASE WHEN precio_direccion_min IS NULL THEN 1 ELSE 0 END) AS Nulos_DirMin
FROM dbo.PreciosCalculados;
GO

PRINT ''
PRINT '=== VALIDACIÓN COMPLETADA ==='
PRINT ''
