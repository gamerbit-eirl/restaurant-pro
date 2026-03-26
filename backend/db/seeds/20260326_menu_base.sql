-- Seed base: menu y adicionales (segun pizarras)
USE restaurant_pro;

-- Mesas base
INSERT INTO mesas (numero, estado)
VALUES
(1, 'libre'), (2, 'libre'), (3, 'libre'), (4, 'libre'), (5, 'libre'),
(6, 'libre'), (7, 'libre'), (8, 'libre'), (9, 'libre'), (10, 'libre'),
(11, 'libre'), (12, 'libre'), (13, 'libre'), (14, 'libre'), (15, 'libre')
ON DUPLICATE KEY UPDATE estado = VALUES(estado);

-- Entradas
INSERT INTO productos (nombre, precio, categoria, area, control_stock, incluye_entrada, entrada_producto_id)
VALUES
('Entrada del dia', 0.00, 'entrada', 'cocina', 0, 0, NULL),
('Torta de choclo (entrada)', 0.00, 'entrada', 'cocina', 0, 0, NULL)
ON DUPLICATE KEY UPDATE
precio = VALUES(precio),
categoria = VALUES(categoria),
area = VALUES(area),
control_stock = VALUES(control_stock),
incluye_entrada = VALUES(incluye_entrada);

-- Menu del dia (con entrada)
INSERT INTO productos (nombre, precio, categoria, area, control_stock, incluye_entrada, entrada_producto_id)
VALUES
('Chanfainita (menu del dia)', 10.00, 'fondo', 'cocina', 0, 1, NULL),
('Cau-cau (menu del dia)', 10.00, 'fondo', 'cocina', 0, 1, NULL),
('Bistec a lo pobre (menu del dia)', 12.00, 'fondo', 'cocina', 0, 1, NULL),
('Tortilla de raya (menu del dia)', 12.00, 'fondo', 'cocina', 0, 1, NULL),
('Seco de res (menu del dia)', 15.00, 'fondo', 'cocina', 0, 1, NULL)
ON DUPLICATE KEY UPDATE
precio = VALUES(precio),
categoria = VALUES(categoria),
area = VALUES(area),
control_stock = VALUES(control_stock),
incluye_entrada = VALUES(incluye_entrada);

-- Adicionales (sin entrada)
INSERT INTO productos (nombre, precio, categoria, area, control_stock, incluye_entrada, entrada_producto_id)
VALUES
('Papa rellena', 6.00, 'adicional', 'cocina', 0, 0, NULL),
('Papa a la huancaina', 7.00, 'adicional', 'cocina', 0, 0, NULL),
('Torta de choclo (adicional)', 7.00, 'adicional', 'cocina', 0, 0, NULL),
('Ceviche (adicional)', 18.00, 'adicional', 'cocina', 0, 0, NULL)
ON DUPLICATE KEY UPDATE
precio = VALUES(precio),
categoria = VALUES(categoria),
area = VALUES(area),
control_stock = VALUES(control_stock),
incluye_entrada = VALUES(incluye_entrada),
entrada_producto_id = NULL;

-- Barra (para pruebas de separacion cocina/barra)
INSERT INTO productos (nombre, precio, categoria, area, control_stock, incluye_entrada, entrada_producto_id)
VALUES
('Inka Cola personal', 4.50, 'bebida', 'barra', 1, 0, NULL),
('Chicha morada', 5.00, 'bebida', 'barra', 1, 0, NULL)
ON DUPLICATE KEY UPDATE
precio = VALUES(precio),
categoria = VALUES(categoria),
area = VALUES(area),
control_stock = VALUES(control_stock),
incluye_entrada = VALUES(incluye_entrada),
entrada_producto_id = NULL;

-- Vincular entrada automatica del menu del dia
UPDATE productos p
JOIN productos e ON e.nombre = 'Entrada del dia'
SET p.entrada_producto_id = e.id
WHERE p.nombre IN (
  'Chanfainita (menu del dia)',
  'Cau-cau (menu del dia)',
  'Bistec a lo pobre (menu del dia)',
  'Tortilla de raya (menu del dia)',
  'Seco de res (menu del dia)'
);
