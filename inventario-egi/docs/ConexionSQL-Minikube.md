# Guía Técnica de Configuración e Interconexión Segura: Windows Server SQL y Entorno Linux (Minikube)

## 1. Arquitectura y Lógica del Entorno
* **Active Directory (Autenticación Centralizada - `.10`):** Centraliza el control de acceso y las credenciales de los usuarios administrativos (docentes, administradores y responsables técnicos). Siguiendo el principio de mínimo privilegio, los **alumnos no se registran como usuarios de dominio en el AD**, ya que no requieren credenciales de acceso al sistema operativo ni a herramientas de administración de la infraestructura.
* **SQL Server (Datos Relacionales - `.20`):** Almacena de forma estructurada el inventario físico, las ubicaciones y los registros de asignación del ecosistema. Los alumnos figuran estrictamente como **registros de datos (valores/strings/legajos)** dentro de las tablas relacionales de asignación para el control de préstamos, optimizando la gestión de identidades en el servidor.
* **Entorno Minikube (Linux - `.30`):** Aloja los contenedores del backend (Flask) y frontend. Requiere un canal de comunicación seguro y directo hacia el motor de base de datos relacional externo alojado en la VM de Windows a través del puerto estático estandarizado.

---

## 2. Instalación del Entorno de Base de Datos
1. Se instaló el motor **SQL Server Express 2022** como una instancia nativa corriendo en segundo plano como servicio en la máquina virtual Windows Server 2022 (`192.168.1.20`).
2. Se instaló la herramienta de administración gráfica **SQL Server Management Studio 22 (SSMS)**.
3. Durante la inicialización de SSMS, se omitió la sincronización con servicios en la nube (Azure/GitHub) seleccionando la opción *"Omitir y agregar cuentas más tarde"*, manteniendo el entorno de gestión perimetralmente aislado bajo **Autenticación de Windows**.

---

## 3. Resolución de Error Crítico de Infraestructura (WMI Bug `[0x80041010]`)
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
2. En el panel izquierdo, se navegó a: **Configuración de red de SQL Server** -> **Protocolos de ITULAB** (nombre de la instancia asignada).
3. Se hizo clic derecho sobre **TCP/IP** y se seleccionó la opción **Habilitar**.
4. Se accedió a las **Propiedades** de TCP/IP (doble clic) y se navegó hasta la pestaña **Direcciones IP**.
5. Se descendió hasta la sección final de configuración global llamada **IPAll**:
   * **Puertos dinámicos TCP:** Se **borró por completo el valor `0`**, dejándolo totalmente vacío. Esto desactiva el comportamiento predeterminado en el cual SQL Server cambia aleatoriamente de puerto al reiniciarse.
   * **Puerto TCP:** Se ingresó de forma explícita el valor **`1433`**, configurándolo como el canal estático permanente.
6. Se aplicaron los cambios y se procedió a **Reiniciar** el servicio de la instancia `SQL Server (ITULAB)` desde la sección *Servicios de SQL Server* para asentar la nueva configuración en memoria.

---

## 5. Configuración del Firewall Perimetral con Enfoque Zero-Trust
Para garantizar la seguridad de la base de datos y evitar el escaneo o acceso no autorizado desde otros segmentos de la red interna, se implementó una regla de entrada restrictiva en el firewall de Windows Server controlada estrictamente por ámbito de origen.

### Comando Ejecutado en CMD (Administrador):
```cmd
netsh advfirewall firewall add rule name="SQL Server 1433 desde Minikube" dir=in action=allow protocol=TCP localport=1433 remoteip=192.168.1.30
```

### Lógica de Seguridad Aplicada:
El cortafuegos filtrará y descartará de manera automática cualquier paquete de datos dirigido al puerto 1433 que no provenga de la dirección IP específica asignada a la máquina de Minikube (`192.168.1.30`). Cualquier otra máquina o atacante dentro de la red que intente sondear el puerto será bloqueado.

---

## 6. Auditoría y Validación de Conectividad Cruzada
Para verificar de manera científica que las capas de red, el enrutamiento del pfSense, el protocolo TCP/IP de SQL y la regla del firewall cooperan correctamente, se realizó una prueba de sockets desde el sistema Linux cliente.

### Comando de Diagnóstico (Ejecutado en la VM Cloud Linux):
```bash
nc -zv 192.168.1.20 1433
```

### Resultado Obtenido:
```text
Connection to 192.168.1.20 1433 port [tcp/ms-sql-s] succeeded!
```

### Conclusión Técnica:
El puerto responde de forma externa como "abierto" y el firewall concede el paso sin latencia al origen autorizado. La infraestructura queda validada y lista para recibir el despliegue de los manifiestos de Kubernetes (External Services y Endpoints) que comunicarán el Pod de la aplicación en Flask con el motor relacional.

---

## 7. Concepto Técnico: El Puerto de Red 1433
Un **puerto de red** es una interfaz o canal lógico virtual que utiliza un sistema operativo para organizar, segmentar y dirigir el flujo de datos entrantes y salientes a través de una misma dirección IP física. Mientras que la dirección IP identifica a la máquina en la red (`192.168.1.20`), el puerto identifica al proceso o servicio específico que debe procesar esa información.

El **puerto 1433** está asignado y estandarizado internacionalmente por la IANA (*Internet Assigned Numbers Authority*) de forma exclusiva para **Microsoft SQL Server**. Al fijar el puerto y abrirlo en el firewall perimetral:
* Garantizamos un canal predecible y estático para que aplicaciones externas (como Flask) sepan exactamente a qué canal lógico enviar las consultas SQL.
* El sistema operativo Windows Server sabe instantáneamente que todo paquete entrante dirigido al puerto 1433 debe ser entregado al proceso en segundo plano del motor de base de datos relacional, evitando conflictos con otros servicios de la infraestructura (como el puerto 389 de LDAP/Active Directory o el puerto 80/443 de servicios web).