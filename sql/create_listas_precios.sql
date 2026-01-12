-- Tabla para definir las listas de precios con rangos de márgenes
CREATE TABLE ListasPrecios (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre_lista NVARCHAR(100) NOT NULL UNIQUE,
    descripcion NVARCHAR(255),
    margen_min_pct DECIMAL(10,6) NOT NULL, -- Margen mínimo que puede cotizar
    margen_max_pct DECIMAL(10,6) NOT NULL, -- Margen máximo que puede cotizar
    orden_jerarquia INT NOT NULL,
    activa BIT DEFAULT 1,
    fecha_creacion DATETIME DEFAULT GETDATE()
);

-- Insertar las 3 listas de precios con rangos
-- Orden: 3=Vendedor (más alto), 2=Gerencia Comercial (medio), 1=Gerencia (hasta Mark-up)
-- Los márgenes son ADICIONALES al Mark-up base (10%)
-- Mark-up base (10%) es el límite inferior de todos
INSERT INTO ListasPrecios (nombre_lista, descripcion, margen_min_pct, margen_max_pct, orden_jerarquia) VALUES
('Vendedor', 'Lista para vendedores - Rango 90% a 65% sobre Mark-up', 0.65, 0.90, 3),
('Gerencia_Comercial', 'Lista para gerencia comercial - Rango 65% a 40% sobre Mark-up', 0.40, 0.65, 2),
('Gerencia', 'Lista para gerencia - Rango 40% a 10% (Mark-up mínimo)', 0.10, 0.40, 1);

-- Verificar si la columna rol existe, si no, agregarla
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Usuarios' AND COLUMN_NAME = 'rol')
BEGIN
    ALTER TABLE Usuarios ADD rol NVARCHAR(50) DEFAULT 'Vendedor';
END

-- Actualizar el usuario existente
UPDATE Usuarios SET rol = 'Vendedor' WHERE username = 'test';

-- Crear tabla para almacenar las listas de precios calculadas
CREATE TABLE PreciosCalculados (
    id INT IDENTITY(1,1) PRIMARY KEY,
    sku NVARCHAR(100) NOT NULL,
    transporte NVARCHAR(20) NOT NULL,
    landed_cost_mxn DECIMAL(18,2) NOT NULL,
    precio_base_mxn DECIMAL(18,2) NOT NULL, -- Landed Cost con Mark-up (10%)
    precio_vendedor_max DECIMAL(18,2) NOT NULL, -- Precio con 90% margen
    precio_vendedor_min DECIMAL(18,2) NOT NULL, -- Precio con 65% margen
    precio_gerencia_com_max DECIMAL(18,2) NOT NULL, -- Precio con 65% margen
    precio_gerencia_com_min DECIMAL(18,2) NOT NULL, -- Precio con 40% margen
    precio_gerencia_max DECIMAL(18,2) NOT NULL, -- Precio con 40% margen
    precio_gerencia_min DECIMAL(18,2) NOT NULL, -- Precio con 10% margen (Mark-up)
    markup_pct DECIMAL(10,6) NOT NULL,
    fecha_calculo DATETIME DEFAULT GETDATE(),
    CONSTRAINT UQ_SKU_Transporte_Precios UNIQUE(sku, transporte)
);

-- Índices para mejorar rendimiento
CREATE INDEX IX_PreciosCalculados_SKU ON PreciosCalculados(sku);
CREATE INDEX IX_PreciosCalculados_Fecha ON PreciosCalculados(fecha_calculo DESC);
