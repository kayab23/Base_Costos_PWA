-- Create tables for clientes, vendedores and secuencias de cotizacion
CREATE TABLE clientes (
  id INT IDENTITY PRIMARY KEY,
  codigo VARCHAR(50) NOT NULL UNIQUE,
  nombre VARCHAR(255) NOT NULL,
  rfc VARCHAR(30),
  direccion NVARCHAR(MAX),
  contacto VARCHAR(255),
  telefono VARCHAR(50),
  email VARCHAR(255),
  metadatos NVARCHAR(MAX),
  created_at DATETIME DEFAULT GETDATE(),
  updated_at DATETIME DEFAULT GETDATE()
);
CREATE INDEX idx_clientes_nombre ON clientes(nombre);

CREATE TABLE vendedores (
  id INT IDENTITY PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  nombre_completo VARCHAR(255) NOT NULL,
  rol VARCHAR(50),
  email VARCHAR(255),
  telefono VARCHAR(50),
  preferencias NVARCHAR(MAX),
  created_at DATETIME DEFAULT GETDATE(),
  updated_at DATETIME DEFAULT GETDATE()
);
CREATE INDEX idx_vendedores_nombre ON vendedores(nombre_completo);

-- Table to store last used quote numbers per client and vendor
CREATE TABLE cotizacion_secuencias (
  id INT IDENTITY PRIMARY KEY,
  cliente_codigo VARCHAR(50) NULL,
  vendedor_username VARCHAR(50) NULL,
  last_num INT DEFAULT 0,
  updated_at DATETIME DEFAULT GETDATE()
);
CREATE INDEX idx_cotsec_cliente ON cotizacion_secuencias(cliente_codigo);
CREATE INDEX idx_cotsec_vendedor ON cotizacion_secuencias(vendedor_username);
