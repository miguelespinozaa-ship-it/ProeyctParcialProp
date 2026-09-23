-- MS1 — Usuarios/Auth (MySQL 8.0)
-- usuarios (1) ──< (N) direcciones

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    telefono VARCHAR(30),
    rol ENUM('customer', 'delivery', 'admin') NOT NULL,
    restaurante_id VARCHAR(50) NULL,
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_usuarios_rol (rol)
);

CREATE TABLE IF NOT EXISTS direcciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    calle VARCHAR(255) NOT NULL,
    ciudad VARCHAR(100) NOT NULL,
    referencia VARCHAR(255),
    lat DECIMAL(10, 7) NULL,
    lng DECIMAL(10, 7) NULL,
    es_principal BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_direcciones_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_direcciones_usuario (usuario_id)
);

-- Usuarios demo, password "password123" (hash bcrypt).
-- admin va directo por SQL porque /auth/register rechaza rol=admin.
-- restaurante_id es un placeholder: reemplazar por el _id real de Mongo tras correr el seed de MS2.
INSERT INTO usuarios (nombre, email, password_hash, telefono, rol, restaurante_id)
VALUES
    ('Cliente Demo', 'customer@demo.com', '$2b$12$A6Is3FCl1EbUaM4hMx2ZG.CxvtjlMc1AoeIWgrtcFbPDiP5/rZvgm', '999111222', 'customer', NULL),
    ('Repartidor Demo', 'delivery@demo.com', '$2b$12$A6Is3FCl1EbUaM4hMx2ZG.CxvtjlMc1AoeIWgrtcFbPDiP5/rZvgm', '999333444', 'delivery', NULL),
    ('Admin Demo', 'admin@demo.com', '$2b$12$A6Is3FCl1EbUaM4hMx2ZG.CxvtjlMc1AoeIWgrtcFbPDiP5/rZvgm', '999555666', 'admin', 'REPLACE_WITH_RESTAURANT_ID')
ON DUPLICATE KEY UPDATE email = email;
