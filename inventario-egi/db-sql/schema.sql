-- =============================================================
-- schema.sql
-- Base de datos SQL Server
-- =============================================================

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'Inventario')
BEGIN
    CREATE DATABASE Inventario;
END
GO

USE Inventario;
GO

-- -------------------------------------------------------------
-- Tabla: ubicacion
-- -------------------------------------------------------------
CREATE TABLE ubicacion (
    id                  INT           NOT NULL IDENTITY(1,1),
    edificio            VARCHAR(50)   NOT NULL,
    aula                VARCHAR(30)   NOT NULL,
    capacidad_equipos   SMALLINT      NOT NULL DEFAULT 0,
    CONSTRAINT pk_ubicacion PRIMARY KEY (id),
    CONSTRAINT uq_ubicacion UNIQUE (edificio, aula)
);
GO

-- -------------------------------------------------------------
-- Tabla: responsable
-- -------------------------------------------------------------
CREATE TABLE responsable (
    id          INT           NOT NULL IDENTITY(1,1),
    nombre      VARCHAR(100)  NOT NULL,
    apellido    VARCHAR(100)  NOT NULL,
    tipo        VARCHAR(10)   NOT NULL,
    email       VARCHAR(150)  NOT NULL,
    legajo      VARCHAR(20)            DEFAULT NULL,
    telefono    VARCHAR(20)            DEFAULT NULL,
    activo      BIT           NOT NULL DEFAULT 1,
    CONSTRAINT pk_responsable PRIMARY KEY (id),
    CONSTRAINT uq_email  UNIQUE (email),
    CONSTRAINT uq_legajo UNIQUE (legajo),
    CONSTRAINT chk_tipo CHECK (tipo IN ('tecnico','docente','alumno'))
);
GO

-- -------------------------------------------------------------
-- Tabla: equipo
-- -------------------------------------------------------------
CREATE TABLE equipo (
    equipo_id                   VARCHAR(20)   NOT NULL,
    numero_serie                VARCHAR(100)  NOT NULL,
    numero_banco                SMALLINT      NOT NULL,
    ubicacion_id                INT           NOT NULL,
    responsable_id              INT           NOT NULL,
    estado                      VARCHAR(15)   NOT NULL DEFAULT 'activo',
    fecha_alta                  DATE          NOT NULL,
    fecha_ultimo_mantenimiento  DATE                   DEFAULT NULL,
    fecha_proximo_mantenimiento DATE                   DEFAULT NULL,
    observaciones               VARCHAR(MAX)           DEFAULT NULL,
    CONSTRAINT pk_equipo PRIMARY KEY (equipo_id),
    CONSTRAINT uq_numero_serie UNIQUE (numero_serie),
    CONSTRAINT chk_estado_equipo
        CHECK (estado IN ('activo','mantenimiento','reserva','baja')),
    CONSTRAINT fk_equipo_ubicacion
        FOREIGN KEY (ubicacion_id)
        REFERENCES ubicacion(id)
        ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT fk_equipo_responsable
        FOREIGN KEY (responsable_id)
        REFERENCES responsable(id)
        ON UPDATE NO ACTION ON DELETE NO ACTION
);
GO

-- -------------------------------------------------------------
-- Tabla: asignaciones_temporales
-- -------------------------------------------------------------
CREATE TABLE asignaciones_temporales (
    id                  INT           NOT NULL IDENTITY(1,1),
    equipo_id           VARCHAR(20)   NOT NULL,
    responsable_id      INT           NOT NULL,
    fecha_inicio        DATE          NOT NULL,
    fecha_fin_estimada  DATE                   DEFAULT NULL,
    fecha_devolucion    DATE                   DEFAULT NULL,
    estado              VARCHAR(12)   NOT NULL DEFAULT 'activa',
    CONSTRAINT pk_asignaciones PRIMARY KEY (id),
    CONSTRAINT chk_estado_asig
        CHECK (estado IN ('activa','finalizada','vencida')),
    CONSTRAINT fk_asig_equipo
        FOREIGN KEY (equipo_id)
        REFERENCES equipo(equipo_id)
        ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT fk_asig_responsable
        FOREIGN KEY (responsable_id)
        REFERENCES responsable(id)
        ON UPDATE NO ACTION ON DELETE NO ACTION
);
GO

-- -------------------------------------------------------------
-- Tabla: mantenimiento
-- -------------------------------------------------------------
CREATE TABLE mantenimiento (
    id           INT            NOT NULL IDENTITY(1,1),
    equipo_id    VARCHAR(20)    NOT NULL,
    tecnico_id   INT            NOT NULL,
    tipo         VARCHAR(15)    NOT NULL,
    fecha_inicio DATE           NOT NULL,
    fecha_fin    DATE                    DEFAULT NULL,
    descripcion  VARCHAR(MAX)            DEFAULT NULL,
    costo        DECIMAL(10,2)           DEFAULT NULL,
    CONSTRAINT pk_mantenimiento PRIMARY KEY (id),
    CONSTRAINT chk_tipo_mant
        CHECK (tipo IN ('preventivo','correctivo','actualizacion')),
    CONSTRAINT fk_mant_equipo
        FOREIGN KEY (equipo_id)
        REFERENCES equipo(equipo_id)
        ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT fk_mant_tecnico
        FOREIGN KEY (tecnico_id)
        REFERENCES responsable(id)
        ON UPDATE NO ACTION ON DELETE NO ACTION
);
GO
