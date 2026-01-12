-- Tabla para gestionar solicitudes de descuentos especiales
CREATE TABLE SolicitudesAutorizacion (
    id INT IDENTITY(1,1) PRIMARY KEY,
    sku NVARCHAR(100) NOT NULL,
    transporte NVARCHAR(20) NOT NULL,
    solicitante_id INT NOT NULL, -- Usuario que solicita
    nivel_solicitante NVARCHAR(50) NOT NULL, -- Vendedor, Gerencia_Comercial
    precio_propuesto DECIMAL(18,2) NOT NULL, -- Precio que quiere ofrecer
    precio_minimo_actual DECIMAL(18,2) NOT NULL, -- Precio mínimo de su nivel
    descuento_adicional_pct DECIMAL(10,6) NOT NULL, -- % adicional de descuento
    cliente NVARCHAR(255), -- Nombre del cliente
    cantidad INT, -- Cantidad de piezas
    justificacion NVARCHAR(1000) NOT NULL,
    estado NVARCHAR(20) DEFAULT 'Pendiente', -- Pendiente, Aprobada, Rechazada
    autorizador_id INT, -- Usuario que autoriza
    fecha_solicitud DATETIME DEFAULT GETDATE(),
    fecha_respuesta DATETIME,
    comentarios_autorizador NVARCHAR(500),
    CONSTRAINT FK_Solicitud_Solicitante FOREIGN KEY (solicitante_id) REFERENCES Usuarios(usuario_id),
    CONSTRAINT FK_Solicitud_Autorizador FOREIGN KEY (autorizador_id) REFERENCES Usuarios(usuario_id),
    CONSTRAINT CHK_Estado CHECK (estado IN ('Pendiente', 'Aprobada', 'Rechazada'))
);

-- Índices para mejorar rendimiento
CREATE INDEX IX_Solicitudes_Estado ON SolicitudesAutorizacion(estado, fecha_solicitud DESC);
CREATE INDEX IX_Solicitudes_Solicitante ON SolicitudesAutorizacion(solicitante_id);
CREATE INDEX IX_Solicitudes_SKU ON SolicitudesAutorizacion(sku);
GO

-- Vista para facilitar consultas con información de usuarios
CREATE VIEW vw_SolicitudesAutorizacion AS
SELECT 
    s.id,
    s.sku,
    s.transporte,
    s.solicitante_id,
    u_sol.username as solicitante,
    s.nivel_solicitante,
    s.precio_propuesto,
    s.precio_minimo_actual,
    s.descuento_adicional_pct,
    s.cliente,
    s.cantidad,
    s.justificacion,
    s.estado,
    s.autorizador_id,
    u_aut.username as autorizador,
    s.fecha_solicitud,
    s.fecha_respuesta,
    s.comentarios_autorizador
FROM SolicitudesAutorizacion s
LEFT JOIN Usuarios u_sol ON s.solicitante_id = u_sol.usuario_id
LEFT JOIN Usuarios u_aut ON s.autorizador_id = u_aut.usuario_id;
