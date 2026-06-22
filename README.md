# 🖥️ Ecosistema de Inventario Seguro — ITU

Proyecto Integrador de la materia **EGI** (Instituto Tecnológico Universitario).  
Sistema centralizado para inventariar las computadoras de los laboratorios de informática, con autenticación federada, firewall perimetral y despliegue en Kubernetes.

---

## 📋 Descripción del Proyecto

La aplicación permite consultar **dónde está** cada equipo y **qué tiene adentro**:

- **SQL Server** almacena la ubicación del equipo (aula, laboratorio, número de banco), el responsable asignado y la fecha de mantenimiento.
- **MongoDB** almacena el hardware del equipo (fabricante, modelo, CPU, RAM, disco, SO, periféricos).
- **Active Directory / LDAP** centraliza la autenticación de todos los usuarios.
- **Flask** es el backend que une todo: autentica contra AD, consulta SQL Server y luego trae los detalles de hardware desde MongoDB.
- **pfSense** actúa como firewall perimetral. Todo el tráfico entrante y saliente del ecosistema pasa obligatoriamente por él.

---

## 🏗️ Arquitectura

```
[Usuario]
    │
    ▼
[Frontend – nginx]
    │
    ▼
[pfSense – Firewall / NAT]   192.168.1.254
    │
    ▼
[VM Ubuntu – Minikube]       192.168.1.30
    │
    ├──► Pod Flask (backend)
    │         │
    │         ├──► MongoDB (Pod en Minikube)        puerto 27017
    │         ├──► SQL Server (VM Windows)           192.168.1.20 : 1433
    │         └──► Active Directory / LDAP           192.168.1.10 : 389
    │
[VM Windows – AD / DNS]      192.168.1.10
[VM Windows – SQL Server]    192.168.1.20
```

### Plan de IPs

| Rol | IP | SO |
|-----|----|----|
| pfSense (Gateway / Firewall) | 192.168.1.254 | pfSense 2.8.1 |
| Active Directory / DNS | 192.168.1.10 | Windows Server 2022 |
| SQL Server / MongoDB | 192.168.1.20 | Windows Server 2022 |
| Minikube / Backend Flask | 192.168.1.30 | Ubuntu |

Todas las VMs operan en **Red Interna aislada** de VirtualBox — ninguna tiene salida directa a internet; todo el tráfico externo pasa por pfSense.

---

## 📁 Estructura del Repositorio

```
inventario-egi/
├── frontend/              → App web (nginx)
│
├── backend/               → App Flask
│   ├── src/
│   ├── Dockerfile
│   └── requirements.txt
│
├── db-sql/                → Scripts de SQL Server (no containerizado)
│   ├── schema.sql         → CREATE TABLE
│   └── seed-data.sql      → INSERT de datos de ejemplo
│
├── db-mongo/              → MongoDB (containerizado en Minikube)
│   ├── seeds/             → Documentos JSON de hardware
│   └── init.js            → Índices opcionales
│
├── kubernetes/            → Manifiestos de Kubernetes
│   ├── namespace.yaml
│   ├── deployments/       → mongo.yaml, flask.yaml
│   ├── services/          → mongo, sql-externo, ldap-externo
│   ├── network-policies/  → Políticas Zero-Trust
│   ├── configmaps/
│   └── secrets/
│
├── docs/                  → Documentación técnica
│   └── red/               → Configuración de red y topología
│
├── README.md
└── .gitignore
```

---

## ⚙️ Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| Backend | Python / Flask |
| Base de datos relacional | SQL Server Express 2022 |
| Base de datos documental | MongoDB |
| Autenticación | Active Directory / LDAP (Windows Server 2022) |
| Orquestación | Kubernetes (Minikube) |
| CNI / Network Policies | Calico |
| Firewall perimetral | pfSense 2.8.1 |
| Servidor web | nginx |
| Cliente de BD | DBeaver |

---

## 🚀 Cómo levantar el entorno

### Requisitos previos

- VirtualBox con las 3 VMs configuradas y en Red Interna (`itu-lan`)
- Minikube iniciado con CNI Calico:

```bash
minikube start --cni=calico
```

### Orden de encendido recomendado

1. VM Active Directory (192.168.1.10)
2. VM SQL Server / MongoDB (192.168.1.20)
3. pfSense (192.168.1.254)
4. VM Ubuntu / Minikube (192.168.1.30)
5. Despliegue de manifiestos Kubernetes
6. Frontend (nginx local)

### Despliegue en Kubernetes

```bash
# Aplicar namespace
kubectl apply -f kubernetes/namespace.yaml

# Desplegar bases de datos y backend
kubectl apply -f kubernetes/deployments/
kubectl apply -f kubernetes/services/

# Aplicar políticas de red (Zero-Trust)
kubectl apply -f kubernetes/network-policies/
```

### Exponer el backend Flask hacia pfSense

```bash
# Desde la VM Ubuntu, ejecutar:
kubectl port-forward deployment/backend-flask 5000:5000 --address 0.0.0.0
```

Luego configurar en pfSense una regla de **NAT Port Forward** apuntando a `192.168.1.30:5000`.

---

## 🔒 Políticas de Red (Zero-Trust)

| Origen | Destino | Puerto | Permitido |
|--------|---------|--------|-----------|
| Internet / Frontend | Flask (vía pfSense) | 5000 | ✅ |
| Flask | SQL Server | 1433 | ✅ |
| Flask | MongoDB | 27017 | ✅ |
| Flask | Active Directory | 389 | ✅ |
| Cualquier otro origen | SQL Server / MongoDB / AD | cualquiera | ❌ |

Las Network Policies de Kubernetes garantizan que **solo Flask** puede alcanzar las bases de datos y el servidor LDAP dentro del namespace.

---

## 🗄️ Modelo de Datos

### SQL Server — Ubicación (`ubicacion-db`)

Almacena dónde está el equipo y a quién le pertenece:

- `equipos` — ID, número de inventario, aula, laboratorio, número de banco
- `responsables` — nombre, rol (docente / alumno / técnico), email
- `asignaciones` — relación equipo ↔ responsable, fecha desde/hasta
- `mantenimientos` — fecha, tipo, técnico responsable

### MongoDB — Hardware (`inventario-db`)

Colección `hardware`, un documento por equipo:

```json
{
  "id_equipo": "EQ-001",
  "tipo": "desktop",
  "fabricante": "Dell",
  "modelo": "OptiPlex 7090",
  "cpu": "Intel Core i5-11500",
  "ram_gb": 16,
  "disco": { "tipo": "SSD", "capacidad_gb": 512 },
  "sistema_operativo": "Windows 11 Pro",
  "monitor": "Dell 24\"",
  "teclado": "Dell KB216",
  "mouse": "Dell MS116"
}
```

---

## 👥 Equipo

| Integrante | Responsabilidad |
|------------|-----------------|
| — | Infraestructura de red / pfSense |
| — | Active Directory / LDAP + integración con SQL Server |
| — | SQL Server (esquema y datos) |
| — | MongoDB + manifiestos Kubernetes (Network Policies) |
| — | Backend Flask + Frontend |

---

## 📄 Documentación adicional

Ver la carpeta [`docs/`](./docs/) para:

- Configuración detallada de red y topología
- Esquema de arquitectura de servicios
- Diagramas de flujo de la aplicación
- Integración Active Directory con SQL Server
- Guía de instalación de SQL Server Express 2022
