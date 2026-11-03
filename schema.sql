-- BODETIME · MySQL 8. Crear la base y el usuario antes de iniciar la aplicación.
CREATE DATABASE IF NOT EXISTS bodetime
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

-- Ejecuta las sentencias siguientes como administrador y cambia la contraseña.
CREATE USER IF NOT EXISTS 'bodetime_app'@'127.0.0.1' IDENTIFIED BY 'cambia_esta_clave';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, ALTER, REFERENCES
  ON bodetime.* TO 'bodetime_app'@'127.0.0.1';
FLUSH PRIVILEGES;

USE bodetime;

CREATE TABLE IF NOT EXISTS trabajadores (
  id_trabajador INT NOT NULL AUTO_INCREMENT,
  codigo VARCHAR(20) NOT NULL,
  nombres VARCHAR(80) NOT NULL,
  apellidos VARCHAR(80) NOT NULL,
  cargo VARCHAR(80) NOT NULL DEFAULT '',
  telefono VARCHAR(30) NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_trabajador),
  CONSTRAINT uq_trabajadores_codigo UNIQUE (codigo),
  INDEX ix_trabajadores_activo_nombre (activo, apellidos, nombres)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS asistencias (
  id_asistencia INT NOT NULL AUTO_INCREMENT,
  id_trabajador INT NOT NULL,
  fecha DATE NOT NULL,
  hora_entrada TIME NOT NULL,
  hora_salida TIME NULL,
  tarde BOOLEAN NOT NULL DEFAULT FALSE,
  observacion VARCHAR(255) NULL,
  PRIMARY KEY (id_asistencia),
  CONSTRAINT uq_asistencia_trabajador_fecha UNIQUE (id_trabajador, fecha),
  CONSTRAINT ck_asistencia_salida_posterior CHECK (hora_salida IS NULL OR hora_salida > hora_entrada),
  CONSTRAINT fk_asistencia_trabajador FOREIGN KEY (id_trabajador)
    REFERENCES trabajadores (id_trabajador) ON DELETE RESTRICT,
  INDEX ix_asistencias_fecha (fecha)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS configuracion_horario (
  id_configuracion INT NOT NULL,
  hora_inicio TIME NOT NULL,
  tolerancia_minutos INT NOT NULL,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id_configuracion),
  CONSTRAINT ck_configuracion_id CHECK (id_configuracion = 1),
  CONSTRAINT ck_configuracion_tolerancia CHECK (tolerancia_minutos BETWEEN 0 AND 240)
) ENGINE=InnoDB;
