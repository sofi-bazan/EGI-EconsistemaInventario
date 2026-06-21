# Guía Técnica de Configuración e Interconexión Segura: Windows Server SQL y Entorno Linux (Minikube)

> **Nota sobre las dos infraestructuras del equipo**
> El proyecto se implementó en paralelo sobre dos entornos con distinta distribución física de las VMs, según los recursos de hardware de cada equipo. La arquitectura lógica es idéntica; solo cambia dónde reside físicamente SQL Server.
>
> | | **Infraestructura A** | **Infraestructura B** |
> |---|---|---|
> | Active Directory / LDAP | `192.168.1.10` | `192.168.1.10` |
> | SQL Server | `192.168.1.10` (junto al AD) | `192.168.1.20` (VM dedicada) |
> | Minikube / Backend Flask | `192.168.1.30` | `192.168.1.30` |
> | Motivo | Límite de RAM (16 GB): AD y SQL conviven | Recursos suficientes para VM separada |
>
> En las secciones siguientes, donde aparece la IP de SQL Server se indican ambas variantes. Cada equipo usa la que corresponde a su infraestructura.

---

## 1. Arquitectura y Lógica del Entorno

* **Active Directory (Autenticación Centralizada - `192.168.1.10`):** Centraliza el control de acceso y las credenciales de los usuarios administrativos (docentes, administradores y responsables técnicos). Siguiendo el principio de mínimo privilegio, los **alumnos no se registran como usuarios de dominio en el AD**, ya que no requieren credenciales de acceso al sistema operativo ni a herramientas de administración de la infraestructura.

* **SQL Server (Datos Relacionales):** Almacena de forma estructurada el inventario físico, las ubicaciones y los registros de asignación del ecosistema. Los alumnos figuran estrictamente como **registros de datos (valores/strings/legajos)** dentro de las tablas relacionales de asignación para el control de préstamos, optimizando la gestión de identidades en el servidor.
    * **Infraestructura A:** SQL Server reside en `192.168.1.10`, en la misma VM Windows Server que el Active Directory. Esta decisión responde al límite de memoria RAM del equipo (16 GB), que no permite ejecutar dos Windows Server simultáneos junto al resto de las VMs. La separación de servicios se mantiene a nivel lógico (cada servicio con su rol y puerto), aunque compartan host.
    * **Infraestructura B:** SQL Server reside en una VM dedicada en `192.168.1.20`, separada del controlador de dominio. Esta es la separación recomendada en entornos productivos.

* **Entorno Minikube (Linux - `192.168.1.30`):** Aloja los contenedores del backend (Flask) y frontend. Requiere un canal de comunicación seguro y directo hacia el motor de base de datos relacional externo alojado en la VM de Windows a través del puerto estático estandarizado.

---

## 2. Instalación del Entorno de Base de Datos

1. Se instaló el motor **SQL Server Express 2022** como una instancia nativa corriendo en segundo plano como servicio en la máquina virtual Windows Server 2022 (`192.168.1.10` en la Infraestructura A / `192.168.1.20` en la Infraestructura B). El nombre de instancia asignado es **ITULAB**.
2. Se instaló la herramienta de administración gráfica **SQL Server Management Studio 22 (SSMS)**.
3. Durante la inicialización de SSMS, se omitió la sincronización con servicios en la nube (Azure/GitHub) seleccionando la opción *"Omitir y agregar cuentas más tarde"*, manteniendo el entorno de gestión perimetralmente aislado bajo **Autenticación de Windows**.

---

## 3. Resolución de Error Crítico de Infraestructura (WMI Bug `[0x80041010]`)

> **Aplica según el caso.** Este error puede presentarse al inicializar el Administrador de Configuración de SQL Server en Windows Server 2022. No todos los equipos lo experimentan; se documenta porque apareció en una de las infraestructuras y la solución es estándar.

Al intentar inicializar el Administrador de Configuración de SQL Server (*SQL Server Configuration Manager*), se presentó un fallo clásico de comunicación con el proveedor WMI de Windows debido a un registro incorrecto de las librerías durante la instalación (asociado a fluctuaciones o microcortes de red).

### Solución Técnica Aplicada:
Se forzó la recompilación manual del archivo de configuración de objetos administrados (`.mof`) actualizado para la versión interna `160` (SQL Server 2022):

1. Se abrió la consola de comandos (`cmd`) con **Privilegios de Administrador**.
2. Se ejecutó el comando de reparación apuntando a la arquitectura nativa del sistema:
   ```cmd
   mofcomp "%programfiles(x86)%\Microsoft SQL Server\160\Shared\sqlmgmprovider.mof"
   ```
3. El compilador devolvió el estado de **"Hecho"** tras almacenar correctamente la información en el repositorio, restituyendo de forma inmediata el acceso al Administrador de Configuración.

---

## 4. Habilitación y Fijación del Protocolo TCP/IP

Por defecto, las ediciones Express de Microsoft SQL Server bloquean cualquier tipo de conexión remota externa por razones de seguridad de fábrica. Para habilitar el tráfico de red:

1. Se ejecutó el comando `SQLServerManager16.msc` desde la ventana de Ejecutar (`Win + R`).
2. En el panel izquierdo, se navegó a: **Configuración de red de SQL Server** → **Protocolos de ITULAB** (nombre de la instancia asignada).
3. Se hizo clic derecho sobre **TCP/IP** y se seleccionó la opción **Habilitar**.
4. Se accedió a las **Propiedades** de TCP/IP (doble clic) y se navegó hasta la pestaña **Direcciones IP**.
5. Se descendió hasta la sección final de configuración global llamada **IPAll**:
   * **Puertos dinámicos TCP:** Se **borró por completo el valor existente**, dejándolo totalmente vacío. Esto desactiva el comportamiento predeterminado en el cual SQL Server cambia aleatoriamente de puerto al reiniciarse (en uno de los equipos, este valor era un puerto dinámico como `52399`, lo que impedía que el firewall y Minikube encontraran el servicio).
   * **Puerto TCP:** Se ingresó de forma explícita el valor **`1433`**, configurándolo como el canal estático permanente.
6. Se aplicaron los cambios y se procedió a **Reiniciar** el servicio de la instancia `SQL Server (ITULAB)` desde la sección *Servicios de SQL Server* para asentar la nueva configuración en memoria.

### Verificación de escucha en red
Tras reiniciar el servicio, se confirmó que SQL Server escucha en el puerto 1433 mediante (en CMD de Windows):
```cmd
netstat -an | find "1433"
```
Resultado esperado:
```text
TCP    0.0.0.0:1433    0.0.0.0:0    LISTENING
```

---

## 5. Habilitación del Modo de Autenticación Mixto y del Usuario `sa`

> **Aplica a la Infraestructura A** (y a cualquier instancia instalada solo con Autenticación de Windows). Necesario para que el backend Flask pueda conectarse con usuario y contraseña SQL.

Por defecto, la instancia se instaló en **modo de autenticación solo Windows** (`IsIntegratedSecurityOnly = 1`). En ese modo, el usuario `sa` y cualquier login de tipo SQL son rechazados, sin importar la contraseña. Como el backend (Flask) se conecta mediante un usuario SQL, fue necesario habilitar el **modo mixto** (Windows + SQL).

### Diagnóstico
Se verificó el estado con autenticación de Windows (`-E`):
```cmd
sqlcmd -S localhost -E -Q "SELECT SERVERPROPERTY('IsIntegratedSecurityOnly')"
```
Un resultado de `1` indica modo solo Windows (el `sa` no funciona); `0` indica modo mixto.

### Solución aplicada
1. Cambio del modo a mixto, escribiendo en el registro mediante una consola con privilegios de Administrador:
   ```cmd
   sqlcmd -S localhost -E -Q "EXEC xp_instance_regwrite N'HKEY_LOCAL_MACHINE', N'Software\Microsoft\MSSQLServer\MSSQLServer', N'LoginMode', REG_DWORD, 2"
   ```
2. Habilitación y fijación de contraseña del usuario `sa`:
   ```cmd
   sqlcmd -S localhost -E -Q "ALTER LOGIN sa ENABLE"
   sqlcmd -S localhost -E -Q "ALTER LOGIN sa WITH PASSWORD = '********'"
   ```
3. **Reinicio del servicio** `SQL Server (ITULAB)` para aplicar el cambio de modo (paso obligatorio).
4. Verificación del login:
   ```cmd
   sqlcmd -S localhost -U sa -P ********
   ```
   El acceso al prompt `1>` confirma que el usuario `sa` quedó operativo.

> Nota de seguridad: la contraseña real del `sa` no se incluye en este documento ni debe versionarse en el repositorio. Se gestiona mediante un Secret de Kubernetes para el backend.

---

## 6. Configuración del Firewall Perimetral con Enfoque Zero-Trust

Para garantizar la seguridad de la base de datos y evitar el escaneo o acceso no autorizado desde otros segmentos de la red interna, se implementó una regla de entrada restrictiva en el firewall de Windows Server controlada por ámbito de origen.

### Comando Ejecutado en CMD (Administrador):
```cmd
netsh advfirewall firewall add rule name="SQL Server 1433" dir=in action=allow protocol=TCP localport=1433 remoteip=192.168.1.30
```

Si la regla ya existía sin restricción de origen, se la modificó para aplicar el ámbito:
```cmd
netsh advfirewall firewall set rule name="SQL Server 1433" new remoteip=192.168.1.30
```

### Lógica de Seguridad Aplicada:
El parámetro `remoteip=192.168.1.30` restringe la conexión al puerto 1433 **exclusivamente a la IP de la VM de Minikube** (`192.168.1.30`), que es el único origen legítimo del tráfico hacia la base de datos. Cualquier otra máquina de la red que intente sondear o conectarse al puerto 1433 es descartada automáticamente por el cortafuegos. Esto materializa el principio de **mínimo privilegio en la red**: solo se abre lo estrictamente necesario, hacia el único consumidor autorizado.

> **Importante:** el valor de `remoteip` es la IP de **quien se conecta** (Minikube, `192.168.1.30`), no la del servidor SQL. Este valor es idéntico en ambas infraestructuras, porque en las dos el clúster reside en `192.168.1.30`.

---

## 7. Auditoría y Validación de Conectividad Cruzada

Para verificar que las capas de red, el enrutamiento del pfSense, el protocolo TCP/IP de SQL y la regla del firewall cooperan correctamente, se realizó una prueba de sockets desde el sistema Linux cliente.

### Comando de Diagnóstico (Ejecutado en la VM Linux / Minikube):
```bash
# Infraestructura A (SQL junto al AD):
nc -zv 192.168.1.10 1433

# Infraestructura B (SQL en VM dedicada):
nc -zv 192.168.1.20 1433
```

### Resultado Obtenido:
```text
Connection to 192.168.1.10 1433 port [tcp/ms-sql-s] succeeded!
```

### Conclusión Técnica:
El puerto responde de forma externa como "abierto" y el firewall concede el paso al origen autorizado (`192.168.1.30`). La infraestructura queda validada y lista para recibir el despliegue de los manifiestos de Kubernetes (External Services y Endpoints) que comunican el Pod de la aplicación en Flask con el motor relacional.

---

## 8. Concepto Técnico: El Puerto de Red 1433

Un **puerto de red** es una interfaz o canal lógico virtual que utiliza un sistema operativo para organizar, segmentar y dirigir el flujo de datos entrantes y salientes a través de una misma dirección IP física. Mientras que la dirección IP identifica a la máquina en la red, el puerto identifica al proceso o servicio específico que debe procesar esa información.

El **puerto 1433** está asignado y estandarizado internacionalmente por la IANA (*Internet Assigned Numbers Authority*) de forma exclusiva para **Microsoft SQL Server**. Al fijar el puerto y abrirlo en el firewall perimetral:
* Garantizamos un canal predecible y estático para que aplicaciones externas (como Flask) sepan exactamente a qué canal lógico enviar las consultas SQL.
* El sistema operativo Windows Server sabe instantáneamente que todo paquete entrante dirigido al puerto 1433 debe ser entregado al proceso del motor de base de datos relacional, evitando conflictos con otros servicios de la infraestructura (como el puerto 389 de LDAP/Active Directory o el puerto 80/443 de servicios web).

---

## 9. Integración Active Directory ↔ SQL Server (Autenticación de Usuarios de Base de Datos)

La consigna exige que *"los usuarios de las bases de datos se autentiquen contra el servidor Active Directory/LDAP"*. Esto se resolvió enlazando **grupos de seguridad del dominio** con **logins de SQL Server**, asignando a cada grupo el nivel de permiso correspondiente según el principio de mínimo privilegio.

### Estructura creada en Active Directory
* Unidad Organizativa: `GestionInventario`
* Tres grupos de seguridad globales, con dos usuarios de ejemplo cada uno:

| Perfil | Grupo de AD | Usuarios de ejemplo |
|---|---|---|
| Administrador | `Grupo_BD_Admin` | `admin1`, `admin2` |
| Responsable técnico / carga | `Grupo_BD_Inventario_C` | `tecnico1`, `tecnico2` |
| Profesores | `Grupo_BD_Inventario_R` | `profesor1`, `profesor2` |

### Vinculación con SQL Server (base `Inventario`)
Por cada grupo del AD se creó un Login de SQL Server con Autenticación de Windows, con los siguientes permisos:

| Grupo de AD | Permiso en SQL Server |
|---|---|
| `Grupo_BD_Admin` | Rol de servidor `sysadmin` (administra todo el motor) |
| `Grupo_BD_Inventario_C` | En base `Inventario`: `db_datareader` + `db_datawriter` (lectura y escritura) |
| `Grupo_BD_Inventario_R` | En base `Inventario`: `db_datareader` (solo lectura) |

### Validación de permisos
Se verificaron los roles asignados mediante consulta directa a las vistas del sistema:
```sql
USE Inventario;
SELECT dp.name AS grupo, r.name AS rol_asignado
FROM sys.database_role_members rm
JOIN sys.database_principals dp ON rm.member_principal_id = dp.principal_id
JOIN sys.database_principals r  ON rm.role_principal_id   = r.principal_id
WHERE dp.name LIKE '%Grupo_BD%';
```
Resultado confirmado:
```text
ITU\Grupo_BD_Inventario_C   db_datareader
ITU\Grupo_BD_Inventario_C   db_datawriter
ITU\Grupo_BD_Inventario_R   db_datareader
```
Esto demuestra que el grupo de técnicos puede leer y escribir, mientras que el de profesores solo puede leer, cumpliendo el principio de mínimo privilegio exigido por la consigna.

> Nota técnica: la prueba en vivo con `EXECUTE AS LOGIN` sobre grupos de Windows presenta una limitación conocida de SQL Server (no permite suplantar grupos directamente). Por ello la validación se realizó consultando los roles efectivamente asignados, que es la evidencia equivalente.

---

## 10. Base de Datos `Inventario`

* Nombre de la base en SQL Server: **`Inventario`** (sin guiones, para evitar el uso de corchetes en las consultas). El Service de Kubernetes que la expone se denomina `ubicacion-db`.
* Estructura: 5 tablas relacionales — `ubicacion`, `responsable`, `equipo`, `asignaciones_temporales`, `mantenimiento`.
* La tabla central `equipo` usa `equipo_id` (formato `PC-0001`) como **identificador compartido con MongoDB**: el mismo ID vincula la ubicación (SQL) con los componentes de hardware (Mongo).
* Los scripts `schema.sql` (estructura) y `seed-data.sql` (datos de ejemplo, 12 filas por tabla) se ejecutaron en ese orden desde SSMS. Originalmente diseñados en MySQL, fueron adaptados a sintaxis SQL Server (`IDENTITY` en lugar de `AUTO_INCREMENT`, `BIT` en lugar de `TINYINT(1)`, restricciones `CHECK` en lugar de `ENUM`, `SET IDENTITY_INSERT` para la carga de IDs explícitos).

---

## 11. Estado y Próximos Pasos

**Completado:**
- SQL Server instalado, con TCP/IP en puerto 1433 fijo y modo mixto habilitado.
- Firewall de Windows restringido al origen `192.168.1.30` (Minikube).
- Conectividad validada desde Minikube (`nc` → `succeeded`).
- Base `Inventario` creada y poblada.
- Integración AD ↔ SQL completa: grupos, usuarios, logins y permisos verificados.

**Pendiente (capa de Kubernetes):**
- External Service + Endpoints `ubicacion-db` → SQL (`192.168.1.10:1433` en Infra A / `192.168.1.20:1433` en Infra B).
- External Service + Endpoints `ldap-service` → AD (`192.168.1.10:389`).
- Secret de Kubernetes con las credenciales de SQL (no versionado en el repo).
- Network Policies (Zero-Trust) una vez desplegado el Pod de Flask.