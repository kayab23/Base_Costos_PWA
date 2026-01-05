-- Esquema inicial para Base Costos (SQL Server)
-- Ejecuta este script en una base de datos vacía o dentro de un schema dedicado (por defecto dbo)

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;

IF OBJECT_ID('dbo.ListaPrecios', 'U') IS NOT NULL DROP TABLE dbo.ListaPrecios;
IF OBJECT_ID('dbo.LandedCostCache', 'U') IS NOT NULL DROP TABLE dbo.LandedCostCache;
IF OBJECT_ID('dbo.PoliticasMargen', 'U') IS NOT NULL DROP TABLE dbo.PoliticasMargen;
IF OBJECT_ID('dbo.TiposCambio', 'U') IS NOT NULL DROP TABLE dbo.TiposCambio;
IF OBJECT_ID('dbo.ParametrosImportacion', 'U') IS NOT NULL DROP TABLE dbo.ParametrosImportacion;
IF OBJECT_ID('dbo.CostosBase', 'U') IS NOT NULL DROP TABLE dbo.CostosBase;
IF OBJECT_ID('dbo.Productos', 'U') IS NOT NULL DROP TABLE dbo.Productos;
IF OBJECT_ID('dbo.ControlVersiones', 'U') IS NOT NULL DROP TABLE dbo.ControlVersiones;
IF OBJECT_ID('dbo.Usuarios', 'U') IS NOT NULL DROP TABLE dbo.Usuarios;
IF OBJECT_ID('dbo.Versiones', 'U') IS NOT NULL DROP TABLE dbo.Versiones;

CREATE TABLE dbo.Versiones (
    version_id        INT IDENTITY(1,1) PRIMARY KEY,
    nombre            NVARCHAR(100)   NOT NULL,
    descripcion       NVARCHAR(500)   NULL,
    creado_por        NVARCHAR(100)   NOT NULL,
    fuente            NVARCHAR(50)    NOT NULL DEFAULT 'excel',
    creado_en         DATETIME2(0)    NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE dbo.Usuarios (
    usuario_id        INT IDENTITY(1,1) PRIMARY KEY,
    username          NVARCHAR(100)   NOT NULL UNIQUE,
    password_hash     NVARCHAR(255)   NOT NULL,
    rol               NVARCHAR(50)    NOT NULL DEFAULT 'operador',
    es_activo         BIT             NOT NULL DEFAULT 1,
    creado_en         DATETIME2(0)    NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE dbo.Productos (
    sku               NVARCHAR(40)    NOT NULL PRIMARY KEY,
    descripcion       NVARCHAR(500)   NOT NULL,
    proveedor         NVARCHAR(150)   NULL,
    modelo            NVARCHAR(200)   NULL,
    origen            NVARCHAR(50)    NULL,
    categoria         NVARCHAR(100)   NULL,
    unidad            NVARCHAR(20)    NULL,
    moneda_base       NCHAR(3)        NOT NULL DEFAULT 'USD',
    activo            BIT             NOT NULL DEFAULT 1,
    notas             NVARCHAR(500)   NULL,
    version_id        INT             NULL REFERENCES dbo.Versiones(version_id),
    actualizado_en    DATETIME2(0)    NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE dbo.CostosBase (
    costo_id          INT IDENTITY(1,1) PRIMARY KEY,
    sku               NVARCHAR(40)    NOT NULL REFERENCES dbo.Productos(sku),
    costo_base        DECIMAL(18,6)   NULL,
    moneda            NCHAR(3)        NOT NULL,
    fecha_actualizacion DATE          NULL,
    notas             NVARCHAR(500)   NULL,
    proveedor         NVARCHAR(150)   NULL,
    version_id        INT             NULL REFERENCES dbo.Versiones(version_id),
    actualizado_en    DATETIME2(0)    NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE dbo.ParametrosImportacion (
    parametro_id      INT IDENTITY(1,1) PRIMARY KEY,
    concepto          NVARCHAR(100)   NOT NULL,
    tipo              NVARCHAR(20)    NOT NULL,
    valor             DECIMAL(18,6)   NOT NULL,
    descripcion       NVARCHAR(500)   NULL,
    notas             NVARCHAR(500)   NULL,
    vigente_desde     DATE            NOT NULL DEFAULT CONVERT(date, SYSUTCDATETIME()),
    vigente_hasta     DATE            NULL,
    version_id        INT             NULL REFERENCES dbo.Versiones(version_id)
);
CREATE UNIQUE INDEX UX_ParamConceptoVigencia
    ON dbo.ParametrosImportacion(concepto, vigente_desde) WHERE vigente_hasta IS NULL;

CREATE TABLE dbo.TiposCambio (
    tasa_id           INT IDENTITY(1,1) PRIMARY KEY,
    moneda            NCHAR(3)        NOT NULL,
    fecha             DATE            NOT NULL,
    tipo_cambio_mxn   DECIMAL(18,6)   NOT NULL,
    fuente            NVARCHAR(100)   NOT NULL,
    version_id        INT             NULL REFERENCES dbo.Versiones(version_id)
);
CREATE UNIQUE INDEX UX_TipoCambioMonedaFecha
    ON dbo.TiposCambio(moneda, fecha);

CREATE TABLE dbo.PoliticasMargen (
    politica_id       INT IDENTITY(1,1) PRIMARY KEY,
    tipo_cliente      NVARCHAR(100)   NOT NULL,
    margen            DECIMAL(9,6)    NOT NULL,
    notas             NVARCHAR(500)   NULL,
    vigente_desde     DATE            NOT NULL DEFAULT CONVERT(date, SYSUTCDATETIME()),
    vigente_hasta     DATE            NULL,
    version_id        INT             NULL REFERENCES dbo.Versiones(version_id)
);
CREATE UNIQUE INDEX UX_MargenClienteVigencia
    ON dbo.PoliticasMargen(tipo_cliente, vigente_desde) WHERE vigente_hasta IS NULL;

CREATE TABLE dbo.LandedCostCache (
    cache_id          INT IDENTITY(1,1) PRIMARY KEY,
    sku               NVARCHAR(40)    NOT NULL REFERENCES dbo.Productos(sku),
    transporte        NVARCHAR(50)    NOT NULL,
    origen            NVARCHAR(50)    NULL,
    moneda_base       NCHAR(3)        NOT NULL,
    costo_base        DECIMAL(18,6)   NULL,
    tc_mxn            DECIMAL(18,6)   NULL,
    costo_base_mxn    DECIMAL(18,6)   NULL,
    flete_pct         DECIMAL(9,6)    NULL,
    seguro_pct        DECIMAL(9,6)    NULL,
    arancel_pct       DECIMAL(9,6)    NULL,
    gastos_aduana_mxn DECIMAL(18,6)   NULL,
    landed_cost_mxn   DECIMAL(18,6)   NULL,
    version_id        INT             NULL REFERENCES dbo.Versiones(version_id),
    calculado_en      DATETIME2(0)    NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE INDEX IX_LandedCostSkuTransporte ON dbo.LandedCostCache(sku, transporte);

CREATE TABLE dbo.ListaPrecios (
    lista_id          INT IDENTITY(1,1) PRIMARY KEY,
    sku               NVARCHAR(40)    NOT NULL REFERENCES dbo.Productos(sku),
    tipo_cliente      NVARCHAR(100)   NOT NULL,
    moneda_precio     NCHAR(3)        NOT NULL,
    tc_mxn            DECIMAL(18,6)   NULL,
    landed_cost_mxn   DECIMAL(18,6)   NULL,
    margen_pct        DECIMAL(9,6)    NULL,
    precio_venta_mxn  DECIMAL(18,6)   NULL,
    precio_venta_moneda DECIMAL(18,6) NULL,
    precio_min_mxn    DECIMAL(18,6)   NULL,
    notas             NVARCHAR(500)   NULL,
    version_id        INT             NULL REFERENCES dbo.Versiones(version_id),
    calculado_en      DATETIME2(0)    NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE INDEX IX_ListaPreciosSkuCliente ON dbo.ListaPrecios(sku, tipo_cliente);

CREATE TABLE dbo.ControlVersiones (
    control_id        INT IDENTITY(1,1) PRIMARY KEY,
    fecha             DATETIME2(0)    NOT NULL,
    version           NVARCHAR(50)    NOT NULL,
    cambio            NVARCHAR(500)   NOT NULL,
    responsable       NVARCHAR(100)   NOT NULL
);
