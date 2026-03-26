-- Restaurant Pro - Orders module migration
-- Date: 2026-03-26

CREATE DATABASE IF NOT EXISTS restaurant_pro CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE restaurant_pro;

CREATE TABLE IF NOT EXISTS mesas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero INT NOT NULL UNIQUE,
    estado VARCHAR(20) NOT NULL DEFAULT 'libre'
);

CREATE TABLE IF NOT EXISTS productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    precio DECIMAL(10,2) NOT NULL,
    categoria VARCHAR(50) NULL,
    area VARCHAR(20) NOT NULL DEFAULT 'cocina',
    control_stock TINYINT(1) NOT NULL DEFAULT 0,
    incluye_entrada TINYINT(1) NOT NULL DEFAULT 0,
    entrada_producto_id INT NULL,
    CONSTRAINT fk_productos_entrada FOREIGN KEY (entrada_producto_id) REFERENCES productos(id)
);

CREATE TABLE IF NOT EXISTS pedidos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mesa_id INT NOT NULL,
    mesa_activa INT NULL UNIQUE,
    estado VARCHAR(20) NOT NULL DEFAULT 'abierto',
    fecha_apertura DATETIME NOT NULL,
    fecha_cierre DATETIME NULL,
    INDEX ix_pedidos_mesa_id (mesa_id),
    INDEX ix_pedidos_estado (estado),
    CONSTRAINT fk_pedidos_mesa FOREIGN KEY (mesa_id) REFERENCES mesas(id)
);

CREATE TABLE IF NOT EXISTS pedido_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    tipo_consumo VARCHAR(20) NOT NULL,
    area VARCHAR(20) NOT NULL,
    estado_item VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    hora_envio_cocina DATETIME NULL,
    hora_listo DATETIME NULL,
    hora_entrega DATETIME NULL,
    creado_en DATETIME NOT NULL,
    INDEX ix_pedido_items_pedido_id (pedido_id),
    INDEX ix_pedido_items_producto_id (producto_id),
    INDEX ix_pedido_items_estado_item (estado_item),
    CONSTRAINT fk_items_pedido FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    CONSTRAINT fk_items_producto FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- Safe upgrades for existing schemas
ALTER TABLE productos ADD COLUMN IF NOT EXISTS incluye_entrada TINYINT(1) NOT NULL DEFAULT 0;
ALTER TABLE productos ADD COLUMN IF NOT EXISTS entrada_producto_id INT NULL;
ALTER TABLE productos ADD COLUMN IF NOT EXISTS area VARCHAR(20) NOT NULL DEFAULT 'cocina';
ALTER TABLE productos MODIFY COLUMN precio DECIMAL(10,2) NOT NULL;

ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS mesa_activa INT NULL UNIQUE;
ALTER TABLE pedidos MODIFY COLUMN mesa_id INT NOT NULL;
ALTER TABLE pedidos MODIFY COLUMN estado VARCHAR(20) NOT NULL DEFAULT 'abierto';

ALTER TABLE pedido_items ADD COLUMN IF NOT EXISTS area VARCHAR(20) NOT NULL DEFAULT 'cocina';
ALTER TABLE pedido_items ADD COLUMN IF NOT EXISTS hora_entrega DATETIME NULL;
ALTER TABLE pedido_items ADD COLUMN IF NOT EXISTS creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE pedido_items MODIFY COLUMN cantidad INT NOT NULL;
ALTER TABLE pedido_items MODIFY COLUMN precio_unitario DECIMAL(10,2) NOT NULL;
ALTER TABLE pedido_items MODIFY COLUMN tipo_consumo VARCHAR(20) NOT NULL;
ALTER TABLE pedido_items MODIFY COLUMN estado_item VARCHAR(20) NOT NULL DEFAULT 'pendiente';
