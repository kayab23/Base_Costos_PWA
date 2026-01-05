IF OBJECT_ID('dbo.Usuarios', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Usuarios (
        usuario_id        INT IDENTITY(1,1) PRIMARY KEY,
        username          NVARCHAR(100)   NOT NULL UNIQUE,
        password_hash     NVARCHAR(255)   NOT NULL,
        rol               NVARCHAR(50)    NOT NULL DEFAULT 'operador',
        es_activo         BIT             NOT NULL DEFAULT 1,
        creado_en         DATETIME2(0)    NOT NULL DEFAULT SYSUTCDATETIME()
    );
END;
