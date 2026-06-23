-- =============================================================
-- seed-data.sql
-- Datos de ejemplo
-- =============================================================

USE Inventario;
GO

-- -------------------------------------------------------------
-- Limpieza opcional para poder re-ejecutar el seed.
-- Se borra en orden inverso a las dependencias.
-- -------------------------------------------------------------
DELETE FROM mantenimiento;
DELETE FROM asignaciones_temporales;
DELETE FROM equipo;
DELETE FROM responsable;
DELETE FROM ubicacion;
GO

-- -------------------------------------------------------------
-- 1) ubicacion 
-- -------------------------------------------------------------
SET IDENTITY_INSERT ubicacion ON;
INSERT INTO ubicacion (id, edificio, aula, capacidad_equipos) VALUES
    (1,  'Pabellon A', 'Lab 1 - Informatica', 30),
    (2,  'Pabellon A', 'Lab 2 - Redes',       25),
    (3,  'Pabellon A', 'Lab 3 - Sistemas',    25),
    (4,  'Pabellon B', 'Lab 4 - Hardware',    20),
    (5,  'Pabellon B', 'Lab 5 - Multimedia',  28),
    (6,  'Pabellon B', 'Aula 10 - Teoria',    40),
    (7,  'Pabellon C', 'Lab 6 - Programacion',30),
    (8,  'Pabellon C', 'Lab 7 - Base Datos',  22),
    (9,  'Pabellon C', 'Aula 12 - Teoria',    35),
    (10, 'Pabellon D', 'Lab 8 - Redes II',    25),
    (11, 'Pabellon D', 'Deposito Tecnico',    50),
    (12, 'Pabellon D', 'Sala Servidores',     15);
SET IDENTITY_INSERT ubicacion OFF;
GO

-- -------------------------------------------------------------
-- 2) responsable 
-- -------------------------------------------------------------
SET IDENTITY_INSERT responsable ON;
INSERT INTO responsable (id, nombre, apellido, tipo, email, legajo, telefono, activo) VALUES
    (1,  'Carlos',  'Garcia',    'tecnico', 'cgarcia@itu.edu.ar',    'TEC-001', '261-4001001', 1),
    (2,  'Marina',  'Perez',     'tecnico', 'mperez@itu.edu.ar',     'TEC-002', '261-4001002', 1),
    (3,  'Diego',   'Martinez',  'tecnico', 'dmartinez@itu.edu.ar',  'TEC-003', '261-4001003', 1),
    (4,  'Laura',   'Fernandez', 'tecnico', 'lfernandez@itu.edu.ar', 'TEC-004', '261-4001004', 1),
    (5,  'Roberto', 'Sosa',      'docente', 'rsosa@itu.edu.ar',      'DOC-101', '261-4002001', 1),
    (6,  'Andrea',  'Gomez',     'docente', 'agomez@itu.edu.ar',     'DOC-102', '261-4002002', 1),
    (7,  'Pablo',   'Luna',      'docente', 'pluna@itu.edu.ar',      'DOC-103', '261-4002003', 1),
    (8,  'Silvia',  'Romero',    'docente', 'sromero@itu.edu.ar',    'DOC-104', '261-4002004', 1),
    (9,  'Nicolas', 'Diaz',      'alumno',  'ndiaz@itu.edu.ar',      'ALU-2201',NULL,          1),
    (10, 'Julieta', 'Castro',    'alumno',  'jcastro@itu.edu.ar',    'ALU-2202',NULL,          1),
    (11, 'Tomas',   'Herrera',   'alumno',  'therrera@itu.edu.ar',   'ALU-2203',NULL,          1),
    (12, 'Camila',  'Ortiz',     'alumno',  'cortiz@itu.edu.ar',     'ALU-2204',NULL,          0);
SET IDENTITY_INSERT responsable OFF;
GO

-- -------------------------------------------------------------
-- 3) equipo 
-- -------------------------------------------------------------
INSERT INTO equipo
    (equipo_id, numero_serie, numero_banco, ubicacion_id, responsable_id,
     estado, fecha_alta, fecha_ultimo_mantenimiento, fecha_proximo_mantenimiento, observaciones) VALUES
    ('PC-0001', 'SN-LN-2024-0001',  1,  1, 1, 'activo',        '2024-03-01', '2025-03-01', '2026-03-01', 'Equipo de catedra'),
    ('PC-0002', 'SN-HP-2024-0002',  2,  1, 1, 'activo',        '2024-03-01', '2025-03-01', '2026-03-01', NULL),
    ('PC-0003', 'SN-DL-2024-0003',  3,  2, 2, 'activo',        '2024-04-15', '2025-04-15', '2026-04-15', NULL),
    ('PC-0004', 'SN-LN-2024-0004',  1,  2, 2, 'mantenimiento', '2024-04-15', '2026-01-10', '2026-07-10', 'Falla intermitente de fuente'),
    ('PC-0005', 'SN-HP-2024-0005',  4,  3, 1, 'activo',        '2024-05-20', '2025-05-20', '2026-05-20', NULL),
    ('PC-0006', 'SN-AS-2024-0006',  5,  4, 3, 'activo',        '2024-06-10', '2025-06-10', '2026-06-10', 'Banco de pruebas hardware'),
    ('PC-0007', 'SN-DL-2024-0007',  2,  5, 3, 'reserva',       '2024-06-10', NULL,         '2026-06-10', 'Sin asignar aun'),
    ('PC-0008', 'SN-LN-2024-0008',  6,  7, 4, 'activo',        '2024-07-01', '2025-07-01', '2026-07-01', NULL),
    ('PC-0009', 'SN-HP-2024-0009',  1,  8, 4, 'activo',        '2024-07-01', '2025-07-01', '2026-07-01', 'Equipo lab base de datos'),
    ('PC-0010', 'SN-AS-2024-0010',  3, 10, 2, 'activo',        '2024-08-12', '2025-08-12', '2026-08-12', NULL),
    ('PC-0011', 'SN-DL-2024-0011',  7, 11, 1, 'baja',          '2022-02-01', '2024-02-01', NULL,         'Dado de baja por obsolescencia'),
    ('PC-0012', 'SN-LN-2024-0012',  1, 12, 3, 'activo',        '2024-09-05', '2025-09-05', '2026-09-05', 'Servidor de practicas');
GO

-- -------------------------------------------------------------
-- 4) asignaciones_temporales
-- -------------------------------------------------------------
SET IDENTITY_INSERT asignaciones_temporales ON;
INSERT INTO asignaciones_temporales
    (id, equipo_id, responsable_id, fecha_inicio, fecha_fin_estimada, fecha_devolucion, estado) VALUES
    (1,  'PC-0001', 5,  '2026-03-01', '2026-07-01', NULL,         'activa'),
    (2,  'PC-0002', 6,  '2026-03-01', '2026-07-01', NULL,         'activa'),
    (3,  'PC-0003', 9,  '2025-08-01', '2025-12-01', '2025-11-28', 'finalizada'),
    (4,  'PC-0005', 7,  '2026-03-15', '2026-07-15', NULL,         'activa'),
    (5,  'PC-0006', 10, '2025-09-01', '2025-12-15', '2025-12-10', 'finalizada'),
    (6,  'PC-0008', 8,  '2026-04-01', '2026-08-01', NULL,         'activa'),
    (7,  'PC-0009', 11, '2025-04-01', '2025-07-01', NULL,         'vencida'),
    (8,  'PC-0010', 12, '2025-08-15', '2025-12-15', '2025-12-20', 'finalizada'),
    (9,  'PC-0001', 9,  '2025-03-01', '2025-07-01', '2025-06-30', 'finalizada'),
    (10, 'PC-0012', 5,  '2026-09-05', '2026-12-05', NULL,         'activa'),
    (11, 'PC-0004', 10, '2025-04-15', '2025-08-15', NULL,         'vencida'),
    (12, 'PC-0002', 11, '2026-04-01', '2026-08-01', NULL,         'activa');
SET IDENTITY_INSERT asignaciones_temporales OFF;
GO

-- -------------------------------------------------------------
-- 5) mantenimiento
-- -------------------------------------------------------------
SET IDENTITY_INSERT mantenimiento ON;
INSERT INTO mantenimiento
    (id, equipo_id, tecnico_id, tipo, fecha_inicio, fecha_fin, descripcion, costo) VALUES
    (1,  'PC-0001', 1, 'preventivo',    '2025-03-01', '2025-03-01', 'Limpieza general y actualizacion de drivers', 0.00),
    (2,  'PC-0002', 1, 'preventivo',    '2025-03-01', '2025-03-02', 'Limpieza y cambio de pasta termica',          0.00),
    (3,  'PC-0003', 2, 'correctivo',    '2025-04-15', '2025-04-16', 'Reemplazo de disco por SSD',              45000.00),
    (4,  'PC-0004', 2, 'correctivo',    '2026-01-10', NULL,         'Diagnostico de falla de fuente (en curso)',  NULL),
    (5,  'PC-0005', 1, 'actualizacion', '2025-05-20', '2025-05-20', 'Ampliacion de RAM a 16 GB',               28000.00),
    (6,  'PC-0006', 3, 'preventivo',    '2025-06-10', '2025-06-10', 'Revision de banco de pruebas',                0.00),
    (7,  'PC-0008', 4, 'preventivo',    '2025-07-01', '2025-07-01', 'Limpieza y chequeo de temperatura',           0.00),
    (8,  'PC-0009', 4, 'correctivo',    '2025-07-01', '2025-07-03', 'Cambio de fuente de alimentacion',        32000.00),
    (9,  'PC-0010', 2, 'preventivo',    '2025-08-12', '2025-08-12', 'Mantenimiento de rutina semestral',           0.00),
    (10, 'PC-0011', 1, 'correctivo',    '2024-02-01', '2024-02-05', 'Ultimo service antes de baja',            15000.00),
    (11, 'PC-0012', 3, 'actualizacion', '2025-09-05', '2025-09-06', 'Instalacion de SO de practicas',              0.00),
    (12, 'PC-0001', 4, 'correctivo',    '2026-02-01', NULL,         'Reemplazo de teclado defectuoso (en curso)',  NULL);
SET IDENTITY_INSERT mantenimiento OFF;
GO
