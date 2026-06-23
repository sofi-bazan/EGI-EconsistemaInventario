# Ecosistema de Inventario Seguro — ITU

**Proyecto Integrador — Materia EGI**  
Instituto Tecnológico Universitario (ITU) · Dominio: `itu.local`

Sistema centralizado para inventariar las computadoras de los laboratorios de informática, con autenticación federada contra Active Directory, firewall perimetral pfSense y despliegue containerizado en Kubernetes (Minikube).

---

## Descripción del Proyecto

La aplicación permite consultar **dónde está** cada equipo y **qué hardware tiene**:

- **SQL Server** (`192.168.1.20`) — almacena la ubicación del equipo (edificio, aula, número de banco/mesa), el responsable asignado y el historial de mantenimiento.
- **MongoDB** (containerizado en Minikube, `192.168.1.30`) — almacena los componentes de hardware de cada equipo: CPU, RAM, disco, SO, periféricos.
- **Active Directory / LDAP** (`192.168.1.10`) — centraliza la autenticación de todos los usuarios (profesores, técnicos, administradores).
- **Backend Flask** — API containerizada en Kubernetes que une todo: autentica contra AD, consulta SQL Server para obtener la ubicación y luego trae el hardware de MongoDB usando el mismo `equipo_id` como clave compartida entre ambas bases.
- **pfSense** (`192.168.1.254`) — firewall perimetral. Único punto de entrada y salida de la red interna. Todo el tráfico externo pasa obligatoriamente por él.
- **Frontend nginx** — sirve la interfaz web al usuario desde la PC del equipo.

---

## Arquitectura del Sistema

```
[Usuario / Navegador]
         │
         ▼
 [Frontend – nginx]        (PC local del equipo)
         │
         ▼ HTTP
 [pfSense – Firewall/NAT]  192.168.1.254     ← único punto de entrada
         │
         ▼ NAT Port Forward → :5000
 [VM Ubuntu – Minikube]    192.168.1.30
         │
         └──► Pod Flask (backend)
                   │
                   ├──► MongoDB (Pod en Minikube)       :27017
                   ├──► SQL Server (VM Windows)  192.168.1.20:1433
                   └──► Active Directory / LDAP  192.168.1.10:389

 [VM Windows – AD / DNS]   192.168.1.10
 [VM Windows – SQL Server] 192.168.1.20
```

**Flujo principal:** `nginx → pfSense → VM Minikube → Pod Flask → AD (auth) → SQL Server (ubicación) → MongoDB (hardware)`

### Plan de direccionamiento IP

| Equipo / Rol | IP estática | Gateway | DNS | SO |
|---|---|---|---|---|
| pfSense (Firewall / Gateway) | 192.168.1.254 | — | — | pfSense 2.8.1 |
| Active Directory / DNS | 192.168.1.10 | 192.168.1.254 | 127.0.0.1 (sí mismo) | Windows Server 2022 |
| SQL Server / MongoDB | 192.168.1.20 | 192.168.1.254 | 192.168.1.10 (AD) | Windows Server 2022 |
| Minikube / Backend Flask | 192.168.1.30 | 192.168.1.254 | 192.168.1.10 (AD) | Ubuntu |

> **Topología elegida: Red Interna Aislada en VirtualBox.** Se evaluaron dos enfoques (Bridge y Red Interna). Se optó por la Red Interna porque el aislamiento es topológico — ninguna VM tiene adaptador NAT propio — lo que garantiza que pfSense sea el único punto de entrada/salida por diseño físico, no solo por reglas. Esto cumple de forma más fiel el requisito de perímetro obligatorio del enunciado y hace el entorno completamente portable para la defensa sin depender de la red del laboratorio.

---

## Estructura del Repositorio

```
inventario-egi/
├── frontend/                  → App web (nginx, HTML/CSS/JS)
│
├── backend/                   → API Flask (lógica de negocio)
│   ├── src/
│   ├── Dockerfile
│   └── requirements.txt
│
├── db-sql/                    → SQL Server (corre en VM Windows, NO containerizado)
│   ├── schema.sql             → CREATE TABLE (tablas del inventario)
│   └── seed-data.sql          → INSERT de datos de ejemplo
│
├── db-mongo/                  → MongoDB (SÍ containerizado en Minikube)
│   ├── seeds/
│   │   └── hardware.json      → 12 documentos de hardware de ejemplo
│   └── init.js                → Crea colección, validador, índices e inserta seeds
│
├── kubernetes/                → Manifiestos de Kubernetes
│   ├── namespace.yaml         → Namespace aislado "inventario"
│   ├── deployments/
│   │   ├── mongo.yaml         → Deployment de MongoDB
│   │   └── flask.yaml         → Deployment del backend Flask
│   ├── services/
│   │   ├── mongo              → ClusterIP interno para MongoDB
│   │   ├── sql-externo        → ExternalName → 192.168.1.20:1433
│   │   └── ldap-externo       → ExternalName → 192.168.1.10:389
│   ├── network-policies/      → Políticas Zero-Trust (Calico)
│   ├── configmaps/
│   └── secrets/
│
├── docs/                      → Documentación técnica
│   ├── Configuracion_de_Red_EGI.docx
│   ├── Integración_de_AD_con_SQL_Server.pdf
│   ├── Instalación_de_MSSQL_Express_2022.pdf
│   └── Instrucciones_EGI.md
│
├── README.md
└── .gitignore
```

---

## Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Frontend | nginx (HTML, CSS, JS) |
| Backend / API | Python / Flask |
| Base de datos relacional | SQL Server Express 2022 (instancia `ITULAB`) |
| Base de datos documental | MongoDB (imagen oficial, containerizada) |
| Autenticación | Active Directory / LDAP · Windows Server 2022 · dominio `itu.local` |
| Orquestación de contenedores | Kubernetes (Minikube) |
| CNI / Network Policies | Calico |
| Firewall perimetral | pfSense 2.8.1 |
| Virtualización | VirtualBox (Red Interna `itu-lan`) |
| Cliente de BD | DBeaver |

---

## Modelo de Datos

### SQL Server — Base `Inventario` (instancia `ITUSRV002\ITULAB`)

Almacena **dónde está** el equipo y a quién le pertenece. El campo `equipo_id` (formato `PC-0001`) es el identificador compartido con MongoDB.

| Tabla | Descripción |
|---|---|
| `equipo` | ID del equipo, tipo (desktop/laptop), número de inventario |
| `ubicacion` | Edificio, aula/laboratorio, número de banco/mesa, capacidad |
| `responsable` | Nombre, apellido, tipo (técnico/docente), email, legajo |
| `asignaciones_temporales` | Relación equipo ↔ responsable con fechas |
| `mantenimiento` | Fecha, tipo, técnico responsable, observaciones |

### MongoDB — Base `inventario`, colección `hardware`

Almacena **qué tiene adentro** cada equipo. Ejemplo de documento:

```json
{
  "equipo_id": "PC-0001",
  "tipo": "desktop",
  "fabricante": "Lenovo",
  "modelo": "ThinkCentre M75q",
  "cpu": "AMD Ryzen 5 PRO 4650GE @ 3.3GHz",
  "ram_gb": 16,
  "disco_gb": 512,
  "disco_tipo": "ssd",
  "so": "Windows 11 Pro 23H2",
  "monitor": "Samsung 24\" Full HD",
  "mouse": true,
  "teclado": true
}
```

Los seeds incluyen 12 equipos variados: desktops, laptops y servidores de distintos fabricantes (Lenovo, Dell, HP, ASUS).

### Integración entre bases

El backend Flask realiza el **JOIN lógico** entre ambas bases: primero consulta SQL Server por `equipo_id` para obtener la ubicación, luego usa ese mismo ID para traer el hardware de MongoDB.

---

## Modelo de Autenticación y Autorización (Active Directory)

Los accesos se gestionan a nivel de **grupos de AD**, no de usuarios individuales. Esto centraliza la gestión: agregar o quitar acceso a una persona es tan simple como moverla de grupo en el AD, sin tocar SQL Server.

### Estructura en el AD (dominio `itu.local`)

| Perfil | Grupo de AD | Permiso en SQL Server | Usuarios de ejemplo |
|---|---|---|---|
| Administrador del motor | `Grupo_BD_Admin` | `sysadmin` (control total) | AdminAndres, AdminFernando |
| Responsable técnico | `Grupo_BD_Inventario_C` | `db_datareader` + `db_datawriter` | TecMarina, TecCarina |
| Profesores (solo lectura) | `Grupo_BD_Inventario_R` | `db_datareader` | ProfZalazar, ProfOsmel |

### Flujo de autenticación de la aplicación

1. El usuario ingresa sus credenciales en el frontend.
2. Flask realiza una consulta LDAP al AD en `192.168.1.10:389`.
3. Si el usuario existe y la contraseña es válida, se permite el acceso al inventario.

---

## Políticas de Red — Zero-Trust (Kubernetes / Calico)

Las Network Policies garantizan el **principio de mínimo privilegio** dentro del namespace `inventario`.

| Origen | Destino | Puerto | Permitido |
|---|---|---|---|
| Frontend (vía pfSense) | Flask | 5000 | ✅ |
| Flask | MongoDB (Pod) | 27017 | ✅ |
| Flask | SQL Server (VM) | 1433 | ✅ |
| Flask | Active Directory | 389 | ✅ |
| Cualquier otro origen | SQL Server / MongoDB / AD | cualquiera | ❌ |
| MongoDB | cualquier destino | cualquiera | ❌ |

> Todo el tráfico no explícitamente permitido queda bloqueado por defecto. Aunque alguien comprometa el frontend, no puede alcanzar directamente las bases de datos.

### pfSense — NAT Port Forward

La regla en pfSense redirige el tráfico entrante al puerto 5000 de la VM Minikube (`192.168.1.30:5000`), donde `kubectl port-forward` expone el Pod Flask hacia la interfaz de red de la VM.

---

## Cómo Levantar el Entorno

### Requisitos previos

- VirtualBox con las 3 VMs en Red Interna `itu-lan`
- Minikube iniciado con CNI Calico:

```bash
minikube start --cni=calico
```

### Orden de encendido recomendado

1. VM Active Directory / DNS — `192.168.1.10`
2. VM SQL Server / MongoDB — `192.168.1.20`
3. pfSense — `192.168.1.254`
4. VM Ubuntu / Minikube — `192.168.1.30`
5. Despliegue de manifiestos Kubernetes (ver abajo)
6. Frontend nginx (PC local)

### Despliegue en Kubernetes

```bash
# Namespace
kubectl apply -f kubernetes/namespace.yaml

# Deployments y servicios
kubectl apply -f kubernetes/deployments/
kubectl apply -f kubernetes/services/

# Políticas de red Zero-Trust
kubectl apply -f kubernetes/network-policies/
```

### Exponer Flask hacia pfSense

Desde la VM Ubuntu, ejecutar (y dejar corriendo):

```bash
kubectl port-forward deployment/backend-flask 5000:5000 --address 0.0.0.0
```

Luego en pfSense configurar NAT Port Forward apuntando a `192.168.1.30:5000`.

### Verificar la conectividad de red

```bash
# Desde cualquier VM
ping 192.168.1.254   # Gateway pfSense
ping 192.168.1.10    # AD / DNS
ping 192.168.1.20    # SQL Server
ping 192.168.1.30    # Minikube
ping 8.8.8.8         # Salida a internet vía pfSense
```

---

## Equipo

| Integrante | Área / Responsabilidad |
|---|---|
| Sofía Bazán | Infraestructura de red / pfSense / topología VirtualBox |
| Milagros Carrillo | Active Directory, LDAP e integración con SQL Server |
| Julián Méndez | SQL Server (esquema, datos, integración AD) |
| Fernando Castro | MongoDB + manifiestos Kubernetes + Network Policies |

> **Nota sobre ramas de Git:** Fernando Castro no tiene una rama propia en el historial del repositorio. Durante la etapa inicial del proyecto se trabajó sobre `main` directamente, y sus contribuciones fueron integradas mediante merge al branch principal antes de adoptar el flujo de ramas por integrante. Sus aportes (MongoDB, manifiestos K8s y Network Policies) están presentes en el código del repositorio.

---

## Documentación Adicional

Disponible en la carpeta [`docs/`](./docs/):

- `Configuracion_de_Red_EGI.docx` — topología, plan de IPs, configuración de pfSense y VMs, validación de conectividad
- `Integración_de_AD_con_SQL_Server.pdf` — guía paso a paso de la integración AD ↔ SQL Server
- `Instalación_de_MSSQL_Express_2022.pdf` — instalación de SQL Server Express 2022 en Windows Server 2022
- `Instrucciones_EGI.md` — modelo de autenticación, esquema de tablas SQL y validación de permisos