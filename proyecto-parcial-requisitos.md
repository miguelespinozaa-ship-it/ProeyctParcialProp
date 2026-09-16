# PROYECTO PARCIAL: REQUISITOS, ARQUITECTURA Y DIVISIÓN DE TRABAJO (4 PERSONAS)

## 1. Checklist General de Requisitos del Proyecto

### Backend: Microservicios (7 Puntos)

- [ ] **5 Microservicios Dockerizados**:
  - [ ] **MS1 (Usuarios/Auth):** Desarrollado en **Python (FastAPI)** con **MySQL 8.0**. Requiere mínimo 2 tablas SQL relacionadas (`usuarios` 1:N `direcciones`).
  
  - [ ] **MS2 (Catálogo Restaurantes):** Desarrollado en **Java (Spring Boot)** con **MongoDB** (documentos embebidos de platos y reseñas).



  - [ ] **MS3 (Pedidos):** Desarrollado en **Node.js (Express)** con **PostgreSQL 16** (2 tablas relacionadas: `orders` 1:N `order_items`). Consume a MS2 para validar catálogo.

  - [ ] **MS4 (Agregador / Rastreo):** **Sin Base de Datos**. Consume información mediante REST de MS1, MS2 y MS3.

  - [ ] **MS5 (Analítico):** Servicio en **Python (FastAPI)** que ejecuta consultas dinámicas a **AWS Athena** usando `boto3`.

- [ ] **Carga Masiva de Datos Ficticios:** Insertar por única vez mínimo **20,000 registros** en al menos una tabla SQL de MS1 (`usuarios`) y MS3 (`orders`).

- [ ] **Infraestructura de Backend:**
  - [ ] Despliegue con `docker-compose` distribuido en **2 Máquinas Virtuales de Producción** (App Tier).
  - [ ] **Load Balancer Interno (NGINX):** Privado, administrando el balanceo entre ambas MVs de App.
  - [ ] **1 Máquina Virtual de Base de Datos Privada:** Contiene los contenedores de MySQL, PostgreSQL y MongoDB aislados de Internet.
  - [ ] **AWS API Gateway:** Exposición pública de todas las APIs con protocolo **HTTPS**.

- [ ] **Documentación API:** Interfaz Swagger-UI expuesta en los 5 microservicios.

- [ ] **Repositorios:** Enlaces a repositorios públicos de GitHub con todo el código fuente.

### Frontend: Aplicación Web SPA (3 Puntos)

- [ ] Desarrollar una página Web SPA (React/Vue/Angular).
- [ ] Consumir los 5 microservicios invocando **al menos 2 métodos REST por microservicio**.
- [ ] Desplegar la aplicación web en **AWS Amplify** con integración CI/CD desde GitHub.

### Data Science: Ingesta y Analytics (5 Puntos)

- [ ] **Máquina Virtual de Ingesta:** MV dedicada a ejecutar los procesos ETL.
- [ ] **Almacenamiento (Data Lake):** Bucket de AWS S3 para recibir la data en formatos CSV o JSON.
- [ ] **3 Contenedores Docker de Ingesta (Python):** Extracción bajo estrategia Pull (100% de la data) desde MySQL, PostgreSQL y MongoDB cargando archivos al S3.
- [ ] **AWS Glue Data Catalog:** Catálogo de datos configurado para los archivos del S3.
- [ ] **Diagrama ER del Catálogo:** Diagrama Entidad-Relación que vincule las tablas generadas en Glue.
- [ ] **AWS Athena:** Presentar evidencia de mínimo 4 consultas SQL multi-tabla (JOINs) y creación de mínimo 2 Vistas.

### Entregables Adicionales y Exposición (5 Puntos)

- [ ] **Diagrama de Arquitectura de Solución:** Elaborado en `draw.io` incluyendo AWS Amplify, API Gateway, EC2 (App y BD), S3, Glue, Athena y Load Balancer.
- [ ] **Documentos Entregables:** Informe técnico en PDF y presentación resumida en PowerPoint.
- [ ] **Exposición Virtual y Presencial:** Evaluación continua según Hito 1 y Hito 2.

---

## 2. Arquitectura de Solución

La arquitectura sigue un modelo distribuido por capas (Tier Architecture) desplegado en **AWS**:

```
                       [ CLIENTE WEB / NAVEGADOR ]
                                    │
                                    ▼
                          [ AWS Amplify (SPA) ]
                                    │
                                    ▼ (HTTPS Públicos)
                         [ AWS API Gateway ]
                                    │
                                    ▼ (Red Privada / Security Group)
┌────────────────────────────────────────────────────────────────────────┐
│ MVs DE PRODUCCIÓN (EC2 #1 y EC2 #2)                                    │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ NGINX Load Balancer (Privado)                                    │  │
│  └────────────────┬─────────────────────────────────────────────────┘  │
│                   ├──> MS1: Auth / Customers (FastAPI - Python)        │
│                   ├──> MS2: Catalogo Restaurantes (Spring Boot - Java) │
│                   ├──> MS3: Orders / Pedidos (Express - Node.js)       │
│                   ├──> MS4: Aggregator / Tracking (FastAPI - No DB)    │
│                   └──> MS5: Analytics API (FastAPI - Athena Interface)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Tráfico restringido por SG)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ MV BASE DE DATOS (EC2 #3 - Privada)                                    │
│   ├── Container: MySQL 8.0 (MS1 Data)                                  │
│   ├── Container: PostgreSQL 16 (MS3 Data)                              │
│   └── Container: MongoDB (MS2 Data)                                    │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ FLUJO DATA SCIENCE & ANALYTICS                                         │
│                                                                        │
│  [EC2 #4: MV Ingesta]                                                  │
│    ├── Contenedor 1 (ETL MySQL) ────┐                                  │
│    ├── Contenedor 2 (ETL Mongo) ────┼──> [ Bucket S3 Data Lake ]      │
│    └── Contenedor 3 (ETL Postgres) ─┘              │                   │
│                                                    ▼                   │
│                                          [ AWS Glue Data Catalog ]     │
│                                                    │                   │
│                                                    ▼                   │
│                                            [ AWS Athena Engine ]       │
│                                                    │                   │
│                                                    ▼                   │
│                                         [ MS5: API Analítica ]         │
└────────────────────────────────────────────────────────────────────────┘
```

### Componentes de la Arquitectura

1. **Capa de Presentación:** SPA alojada en **AWS Amplify** con CI/CD automático conectado a GitHub.

2. **Capa de Entrada y Seguridad:** **AWS API Gateway** expone públicamente los endpoints HTTPS y enruta el tráfico hacia la red privada.

3. **Capa de Aplicación (2 MVs de Producción):**
   - Contenedores dockerizados de los 5 microservicios.
   - **NGINX** como balanceador de carga interno distribuyendo peticiones entre las 2 instancias EC2.

4. **Capa de Persistencia (1 MV de BD Privada):**
   - Contenedores MySQL, PostgreSQL y MongoDB.
   - La instancia no posee IP pública para bases de datos; solo acepta tráfico del Security Group del App Tier.

5. **Capa de Ingesta y Data Lake:**
   - **MV Ingesta:** Ejecuta 3 contenedores Python que realizan la extracción total de las bases de datos hacia archivos CSV/JSON en **AWS S3**.
   - **AWS Glue:** Escanea el S3 mediante Crawlers para construir la estructura de tablas del catálogo.
   - **AWS Athena & MS5:** Permite ejecutar consultas SQL sobre el Data Lake y servirlas mediante la API REST del MS5.

---

## 3. División de Tareas entre 4 Integrantes

| Integrante | Rol Principal | Enfoque de Entregables |
| --- | --- | --- |
| **Integrante 1** | Backend Engineer & DB Specialist | MS1 (Python + MySQL), MS3 (Node.js + Postgres), Script Carga Masiva (20k), MV BD. |
| **Integrante 2** | Backend & Integration Specialist | MS2 (Java + Mongo), MS4 (Agregador Sin BD), MS5 (Analítico Athena), Swagger UI. |
| **Integrante 3** | Data Engineer & Analytics Specialist | MV Ingesta, 3 Contenedores ETL, S3 Bucket, Glue Catalog, Athena Queries SQL y Vistas. |
| **Integrante 4** | Frontend Developer & Cloud Architect | AWS Amplify (SPA React/Vue), AWS API Gateway, NGINX Load Balancer, Diagrama Draw.io, Reporte/PPT. |

---

### Responsabilidades Detalladas por Integrante

#### Integrante 1: Backend Engineer & DB Specialist

- **Desarrollo MS1 (Auth/Customers):**
  - Configurar FastAPI + MySQL en Docker.
  - Diseñar y aplicar el modelo de 2 tablas SQL relacionadas: `usuarios` (1) a (N) `direcciones`.
  - Crear script `seed.py` para generar **20,000 registros** masivos en la base de datos MySQL.

- **Mantenimiento y Ajuste MS3 (Orders):**
  - Verificar estructura Node.js + Express con PostgreSQL 16 (tablas `orders` 1:N `order_items`).
  - Ejecutar script `seed.js` para asegurar los **20,000 registros** masivos en PostgreSQL.

- **Despliegue Capa de Base de Datos:**
  - Crear el archivo `docker-compose.yml` para la **MV 3 (Base de Datos Privada)** levantando MySQL, PostgreSQL y MongoDB.
  - Configurar la red interna de Docker y volúmenes de almacenamiento persistente (`mysql_data`, `pg_orders_data`, `mongo_data`).

#### Integrante 2: Backend & Integration Specialist

- **Mantenimiento MS2 (Restaurantes):**
  - Asegurar funcionamiento de Spring Boot con MongoDB en puerto 8082 (platos y reseñas embebidas).

- **Desarrollo MS4 (Agregador - Sin Base de Datos):**
  - Construir microservicio en FastAPI o Express sin persistencia de datos.
  - Implementar endpoint `GET /api/v1/tracking/order/{order_id}` consumiendo síncronamente MS1, MS2 y MS3.
  - Implementar endpoint `GET /api/v1/dashboard/customer/{user_id}/summary`.

- **Desarrollo MS5 (Servicio Analítico):**
  - Crear microservicio FastAPI integrando `boto3` para conectar con **AWS Athena**.
  - Crear endpoints `GET /api/v1/analytics/top-restaurants` y `GET /api/v1/analytics/user-metrics` que ejecuten las vistas de Athena.

- **Documentación:**
  - Configurar la especificación OpenAPI / Swagger UI interactiva en los 5 microservicios.

#### Integrante 3: Data Engineer & Analytics Specialist

- **Configuración MV Ingesta & Data Lake:**
  - Crear la máquina virtual EC2 de Ingesta y configurar el bucket en **AWS S3** (`s3://ubereats-datalake-utec/`).

- **Contenedores Docker de Ingesta (ETL Python):**
  - `ingest-mysql`: Extrae `usuarios` y `direcciones` desde MySQL a CSV en S3.
  - `ingest-mongodb`: Extrae `restaurantes` desde MongoDB a JSONL en S3.
  - `ingest-postgres`: Extrae `orders` y `order_items` desde PostgreSQL a CSV en S3.

- **AWS Glue & Diagrama ER:**
  - Configurar Crawlers en AWS Glue Data Catalog para mapear las fuentes cargadas en S3.
  - Generar el Diagrama Entidad-Relación de las tablas del catálogo de datos.

- **AWS Athena (Queries y Vistas):**
  - Redactar el archivo `queries_and_views.sql` con **4 consultas SQL con JOINs multi-tabla**.
  - Crear las **2 Vistas**: `v_resumen_ventas_restaurante` y `v_metricas_usuarios`.

#### Integrante 4: Frontend Developer & Cloud Architect

- **Desarrollo Frontend SPA (AWS Amplify):**
  - Crear aplicación SPA en React/Vue consumiendo los 5 microservicios (mínimo 2 endpoints por servicio):
    - **MS1:** Auth / Login y Datos Perfil.
    - **MS2:** Listar Restaurantes y Ver Menú.
    - **MS3:** Crear Pedido y Listar Pedidos por Usuario.
    - **MS4:** Rastreo de Pedido en Tiempo Real y Dashboard Consolidado.
    - **MS5:** Dashboard de Analítica y Gráficos (Athena).
  - Desplegar en **AWS Amplify** configurando el pipeline con GitHub.

- **Infraestructura Cloud en AWS:**
  - Configurar **AWS API Gateway** (exposición de rutas seguras HTTPS hacia las MVs).
  - Configurar el contenedor **NGINX Load Balancer** en la MV 1 y MV 2.
  - Definir Security Groups (MV BD privada sin acceso público, permitiendo entrada solo desde las MVs de App).

- **Documentación y Entrega:**
  - Diseñar el **Diagrama de Arquitectura de Solución** completo en `draw.io`.
  - Consolidar el informe en Word/PDF y la presentación final en PowerPoint.
