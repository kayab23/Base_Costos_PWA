-- Script de optimización de base de datos para producción
USE BD_Calculo_Costos;
GO

-- Índice en Productos.sku (búsquedas frecuentes)
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Productos_SKU')
    CREATE NONCLUSTERED INDEX IX_Productos_SKU 
    ON dbo.Productos(sku);

-- Índice compuesto en PreciosCalculados
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_PreciosCalculados_SKU_Transporte')
    CREATE NONCLUSTERED INDEX IX_PreciosCalculados_SKU_Transporte 
    ON dbo.PreciosCalculados(sku, transporte);

-- Índice en SolicitudesAutorizacion para filtros por estado
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_SolicitudesAutorizacion_Estado_Solicitante')
    CREATE NONCLUSTERED INDEX IX_SolicitudesAutorizacion_Estado_Solicitante
    ON dbo.SolicitudesAutorizacion(estado, solicitante_id);

-- Índice en Usuarios.username (para login)
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Usuarios_Username')
    CREATE NONCLUSTERED INDEX IX_Usuarios_Username
    ON dbo.Usuarios(username) WHERE es_activo = 1;

-- Verificar índices creados
SELECT 
    t.name AS Tabla,
    i.name AS Indice,
    i.type_desc AS Tipo
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.name IN ('Productos', 'PreciosCalculados', 'SolicitudesAutorizacion', 'Usuarios')
ORDER BY t.name, i.name;

-- Backup manual (ejecutar por separado si es necesario)
-- BACKUP DATABASE BD_Calculo_Costos
-- TO DISK = 'C:\Backups\BD_Calculo_Costos_Manual.bak'
-- WITH FORMAT, NAME = 'Backup Manual Pre-Producción', COMPRESSION;
