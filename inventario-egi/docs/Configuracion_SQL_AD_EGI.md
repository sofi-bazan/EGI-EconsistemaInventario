# Configuración de SQL Server e Integración con Active Directory

**Proyecto Integrador EGI — Ecosistema de Inventario Seguro**
Instituto Tecnológico Universitario (ITU) · Dominio: `itu.local`

---

## 1. Objetivo

Dejar SQL Server Express 2022 operativo, accesible por red desde el clúster de Minikube, y con la autenticación y autorización de usuarios centralizada en Active Directory mediante grupos de dominio. Cada perfil de usuario accede a la base con el mínimo privilegio necesario para su tarea (principio de menor privilegio).

---

## 2. Entorno

| Componente | Detalle |
|---|---|
| Motor de base de datos | SQL Server Express 2022 |
| Instancia | `ITULAB` (acceso: `localhost\ITULAB` o `ITUSRV002.itu.local`) |
| Cliente de administración | SSMS — SQL Server Management Studio 22 |
| VM | Windows Server 2022 (192.168.1.20) |
| Base de datos del proyecto | `Inventario` |
| Dominio | `itu.local` (controlador: 192.168.1.10) |

---

## 3. Habilitación del acceso por red

Por defecto SQL Server Express solo acepta conexiones locales. Para que el backend (Flask, en Minikube) pueda conectarse, se habilitó el acceso por red.

### 3.1. Habilitar el protocolo TCP/IP

Mediante **SQL Server Configuration Manager**:

1. Configuración de red de SQL Server → Protocolos de `ITULAB`.
2. Clic derecho en **TCP/IP** → **Habilitar**.
3. En las propiedades de TCP/IP → pestaña **Direcciones IP** → sección **IPAll** → Puerto TCP: `1433`.
4. Reiniciar el servicio de SQL Server para aplicar el cambio (Servicios de SQL Server → clic derecho → Reiniciar).

### 3.2. Apertura del puerto en el Firewall de Windows

Se abrió el puerto 1433 **únicamente** para la IP del nodo de Minikube (192.168.1.30), respetando el principio de menor privilegio en red:

```
netsh advfirewall firewall add rule name="SQL Server 1433 desde Minikube" dir=in action=allow protocol=TCP localport=1433 remoteip=192.168.1.30
```

### 3.3. Validación de conectividad

Desde la VM de Minikube (Ubuntu) se verificó el acceso al puerto:

```
nc -zv 192.168.1.20 1433
# Resultado esperado: Connection to 192.168.1.20 1433 port [tcp/ms-sql-s] succeeded!
```

---

## 4. Base de datos del proyecto

La base `Inventario` se crea y se puebla mediante dos scripts (versionados en el repositorio, carpeta `db-sql/`):

- `schema.sql` — crea la base y las tablas (estructura).
- `seed-data.sql` — carga los datos de ejemplo.

Orden de ejecución: primero `schema.sql`, luego `seed-data.sql`.

Tablas: `ubicacion`, `responsable`, `equipo`, `asignaciones_temporales`, `mantenimiento`. La tabla central es `equipo`, cuyo campo `equipo_id` (formato `PC-0001`) es el identificador compartido con MongoDB para cruzar la información de ubicación (SQL) con la de hardware (Mongo).

---

## 5. Modelo de autenticación y autorización con Active Directory

Los accesos a la base se resuelven a nivel de **grupos de AD**, no de usuarios individuales. Esto centraliza la gestión: para dar o quitar acceso a una persona, basta con incluirla o quitarla del grupo correspondiente, sin tocar SQL Server.

### 5.1. Perfiles definidos

| Perfil | Grupo de AD | Acceso a la base | Usuarios de ejemplo |
|---|---|---|---|
| Administrador del motor | `Grupo_BD_Admin` | Control total del motor (sysadmin) | AdminAndres, AdminFernando |
| Responsable técnico (carga) | `Grupo_BD_Inventario_C` | Lectura + escritura sobre `Inventario` | TecMarina, TecCarina |
| Profesores (consulta) | `Grupo_BD_Inventario_R` | Solo lectura sobre `Inventario` | ProfZalazar, ProfOsmel |

### 5.2. Configuración en Active Directory

En el controlador de dominio (`ITUSRVDC01`, `itu.local`), dentro de la unidad organizativa `ITU`:

- **Grupos** (OU `ITU > Grupos`): se crearon los tres grupos de seguridad globales: `Grupo_BD_Admin`, `Grupo_BD_Inventario_C`, `Grupo_BD_Inventario_R`.
- **Usuarios** (OU `ITU > Usuarios`): se crearon los usuarios de ejemplo y se incluyó a cada uno en su grupo correspondiente (pestaña *Miembro de*).

### 5.3. Configuración en SQL Server (SSMS)

Por cada grupo de AD se creó un **Login** de tipo *Autenticación de Windows*, enlazado al grupo del dominio. El procedimiento general en SSMS:

1. Seguridad → Inicios de sesión → clic derecho → **Nuevo inicio de sesión**.
2. Autenticación de Windows → **Buscar** → **Tipos de objeto** → marcar **Grupos** → **Ubicaciones** → dominio `itu.local`.
3. Escribir el nombre del grupo → **Comprobar nombres** → Aceptar.
4. Asignar los roles según el perfil (ver tabla siguiente).

| Grupo de AD | Nivel | Roles asignados |
|---|---|---|
| `Grupo_BD_Admin` | Servidor (motor) | `sysadmin` |
| `Grupo_BD_Inventario_C` | Base `Inventario` (Asignación de usuarios) | `db_datareader` + `db_datawriter` |
| `Grupo_BD_Inventario_R` | Base `Inventario` (Asignación de usuarios) | `db_datareader` |

Para los grupos `_C` y `_R` los permisos se asignan en la sección **Asignación de usuarios** del login, seleccionando la base `Inventario` y marcando los roles correspondientes. No se les asigna ningún rol de servidor (no administran el motor).

### 5.4. Roles utilizados (referencia)

| Rol | Nivel | Permite |
|---|---|---|
| `sysadmin` | Servidor | Control total del motor y todas las bases |
| `db_datareader` | Base de datos | Leer todas las tablas (SELECT) |
| `db_datawriter` | Base de datos | Insertar, actualizar y eliminar datos (INSERT, UPDATE, DELETE) |

---

## 6. Validación del control de accesos

Se comprobó que cada perfil accede con el privilegio correcto, ejecutando SSMS con las credenciales de un usuario de cada grupo (clic derecho con Shift → *Ejecutar como otro usuario*, o `runas /user:itu\<usuario> cmd`).

Prueba con un usuario del grupo de solo lectura (profesor):

```sql
USE Inventario;

-- Permitido (lectura):
SELECT * FROM equipo;

-- Denegado (escritura): debe arrojar error de permisos
INSERT INTO ubicacion (edificio, aula, capacidad_equipos)
VALUES ('Prueba', 'Aula Test', 10);
```

Resultado esperado: el `SELECT` devuelve datos; el `INSERT` falla con un error de permiso denegado. Repitiendo la prueba con un usuario del grupo `_C` (técnico), el `INSERT` se ejecuta correctamente. Esto demuestra que los tres niveles de acceso funcionan según lo previsto.

---

## 7. Estado y pendientes

**Completado:**

- SQL Server Express 2022 instalado y operativo en la VM 192.168.1.20.
- Acceso por red habilitado (TCP/IP + puerto 1433 restringido a Minikube).
- Conectividad validada desde el clúster.
- Base `Inventario` creada y poblada con datos de ejemplo.
- Tres grupos de AD creados con sus usuarios.
- Tres logins en SQL enlazados a los grupos, con roles según menor privilegio.
- Control de accesos validado en vivo.

**Pendiente / a coordinar con el equipo:**

- Definir y configurar la autenticación de los **usuarios de la aplicación** contra LDAP (la consigna distingue entre usuarios de las bases —ya resuelto— y usuarios de la app, que consume Flask).
- Hardening de la regla ICMP de la VM (restringir al origen Minikube).
- Confirmar con el equipo que la base relacional definitiva es SQL Server (el diseño original de las tablas fue provisto en sintaxis MySQL y se adaptó a SQL Server).
