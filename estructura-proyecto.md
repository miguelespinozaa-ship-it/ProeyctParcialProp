# Estructura de Repositorio + Flujo de Despliegue (local → GitHub → 2 EC2)

> ⚠️ **Orden obligatorio:** primero TODO corre y se prueba en `docker-compose.dev.yml` (tu máquina, los 5 MS + las 3 BD juntos). Recién cuando el flujo completo funciona local se sube a GitHub y se despliega en las 2 EC2. No se toca AWS antes de tener el local 100% probado (ver [plan-desarrollo.md](plan-desarrollo.md) Fases 1-7 = local, Fase 10 = AWS).

## Flujo general

```
TU MÁQUINA (dev)
   │  git push
   ▼
GitHub (repo público, monorepo)
   │                              │
   │ git clone/pull               │ git clone/pull
   ▼                              ▼
EC2 #1 — App Tier                 EC2 #2 — DB Tier (privada)
docker-compose.app.yml            docker-compose.db.yml
(build + run MS1-MS5 + NGINX)     (run MySQL + Postgres + Mongo)
```

Un solo repo, dos `docker-compose*.yml` distintos. Cada EC2 clona **todo** el repo pero solo levanta el compose que le corresponde — así no hay que mantener 2 repos sincronizados.

## Árbol de archivos (monorepo)

```
proyecto-parcial-cloud/
├── README.md
├── plan-desarrollo.md
├── estructura-proyecto.md
├── proyecto-parcial-requisitos.md
│
├── microservicios/                     # docs de endpoints (ya creados)
│   ├── 00-mapa-conexiones.md
│   ├── MS1-usuarios-auth.md
│   ├── MS2-catalogo-restaurantes.md
│   ├── MS3-pedidos.md
│   ├── MS4-agregador-rastreo.md
│   └── MS5-analitico.md
│
├── docker-compose.app.yml              # ← se corre en EC2 #1
├── docker-compose.db.yml               # ← se corre en EC2 #2
├── docker-compose.dev.yml              # ← se corre EN TU MÁQUINA (todo junto, para probar local)
├── .env.example                        # plantilla; cada EC2 tiene su .env real (no versionado)
│
├── nginx/
│   ├── Dockerfile
│   └── nginx.conf                      # path routing → ms1..ms5
│
├── ms1-usuarios-auth/                  # FastAPI + MySQL
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── seed.py                         # carga masiva 20k
│   └── app/
│       ├── main.py
│       ├── models.py                   # Usuario, Direccion
│       ├── schemas.py
│       ├── routers/
│       │   ├── auth.py
│       │   ├── users.py
│       │   └── addresses.py
│       └── db.py
│
├── ms2-catalogo-restaurantes/          # Spring Boot + MongoDB
│   ├── Dockerfile
│   ├── pom.xml
│   └── src/main/java/com/proyecto/ms2/
│       ├── Ms2Application.java
│       ├── model/Restaurante.java      # con Plato y Resena embebidos
│       ├── controller/RestaurantController.java
│       ├── controller/MenuController.java
│       ├── controller/ReviewController.java
│       └── repository/RestauranteRepository.java
│
├── ms3-pedidos/                        # Express + PostgreSQL
│   ├── Dockerfile
│   ├── package.json
│   ├── seed.js                         # carga masiva 20k
│   └── src/
│       ├── index.js
│       ├── db.js
│       ├── models/ (order.js, orderItem.js)
│       └── routes/
│           ├── orders.js               # crear/listar/status/claim/deliver
│           └── customers.js            # clientes por restaurante
│
├── ms4-agregador-rastreo/              # FastAPI, sin BD
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── clients/ (ms1_client.py, ms2_client.py, ms3_client.py)
│       └── routers/
│           ├── tracking.py
│           └── dashboard.py            # admin/delivery/customer
│
├── ms5-analitico/                      # FastAPI + boto3/Athena
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── athena_client.py
│       └── routers/analytics.py
│
├── db/
│   ├── mysql/init/01-schema.sql        # usuarios, direcciones
│   ├── postgres/init/01-schema.sql     # orders, order_items
│   └── mongo/init/seed-restaurantes.js
│
├── data-science/                       # Integrante 3, EC2 aparte (ingesta)
│   ├── docker-compose.ingest.yml
│   ├── ingest-mysql/
│   ├── ingest-mongodb/
│   ├── ingest-postgres/
│   └── athena/queries_and_views.sql
│
├── frontend/                           # o repo separado si Amplify lo pide así
│   └── (React/Vue SPA)
│
└── infra/
    └── diagramas/                      # draw.io export
```

## `docker-compose.app.yml` (EC2 #1) — solo backends

```yaml
services:
  nginx:
    build: ./nginx
    ports: ["80:80", "443:443"]
    depends_on: [ms1, ms2, ms3, ms4, ms5]

  ms1:
    build: ./ms1-usuarios-auth
    env_file: .env
    environment:
      DB_HOST: ${DB_HOST}        # ← IP PRIVADA de EC2 #2
    ports: ["8081:8081"]

  ms2:
    build: ./ms2-catalogo-restaurantes
    env_file: .env
    environment:
      MONGO_HOST: ${DB_HOST}
    ports: ["8082:8082"]

  ms3:
    build: ./ms3-pedidos
    env_file: .env
    environment:
      PG_HOST: ${DB_HOST}
      MS2_BASE_URL: http://ms2:8082
      MS1_BASE_URL: http://ms1:8081
    ports: ["8083:8083"]

  ms4:
    build: ./ms4-agregador-rastreo
    environment:
      MS1_BASE_URL: http://ms1:8081
      MS2_BASE_URL: http://ms2:8082
      MS3_BASE_URL: http://ms3:8083
    ports: ["8084:8084"]

  ms5:
    build: ./ms5-analitico
    env_file: .env
    ports: ["8085:8085"]
```

No lleva `mysql:`, `postgres:` ni `mongo:` — esos viven solo en `docker-compose.db.yml` (EC2 #2).

## `docker-compose.db.yml` (EC2 #2) — solo bases de datos

```yaml
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: ms1_usuarios
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
      - ./db/mysql/init:/docker-entrypoint-initdb.d
    ports: ["3306:3306"]          # solo accesible vía Security Group privado

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ms3_pedidos
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pg_orders_data:/var/lib/postgresql/data
      - ./db/postgres/init:/docker-entrypoint-initdb.d
    ports: ["5432:5432"]

  mongo:
    image: mongo:7
    volumes:
      - mongo_data:/data/db
      - ./db/mongo/init:/docker-entrypoint-initdb.d
    ports: ["27017:27017"]

volumes:
  mysql_data:
  pg_orders_data:
  mongo_data:
```

No lleva NGINX ni ningún MS — esta VM **no corre código de aplicación**, solo persistencia.

## `docker-compose.dev.yml` (tu máquina)

Junta ambos: los 5 MS + las 3 BD en una sola red docker, para probar todo el flujo end-to-end sin tocar AWS. Es el que usás en las Fases 1-7 del [plan-desarrollo.md](plan-desarrollo.md).

## Pasos de despliegue reales en cada EC2

### EC2 #2 (DB, privada — se levanta primero)
```bash
git clone https://github.com/<user>/proyecto-parcial-cloud.git
cd proyecto-parcial-cloud
cp .env.example .env          # setear passwords reales
docker compose -f docker-compose.db.yml up -d
```
Anotar la **IP privada** de esta instancia → se usa como `DB_HOST` en EC2 #1.

### EC2 #1 (App)
```bash
git clone https://github.com/<user>/proyecto-parcial-cloud.git
cd proyecto-parcial-cloud
cp .env.example .env
# .env: DB_HOST=<ip-privada-ec2-2>
docker compose -f docker-compose.app.yml up -d --build
```

### Actualizar tras cada `git push` (re-deploy)
```bash
git pull
docker compose -f docker-compose.app.yml up -d --build   # en EC2 #1
docker compose -f docker-compose.db.yml up -d             # en EC2 #2 (rara vez cambia)
```

## Security Groups
| EC2 | Inbound permitido |
|---|---|
| EC2 #1 (App) | 80/443 desde API Gateway; 8081-8085 solo si se debug directo |
| EC2 #2 (DB) | 3306, 5432, 27017 **solo** desde el SG de EC2 #1 — nada desde internet |

## `.env` — qué va en cada EC2 (nunca se commitea, solo `.env.example`)

**EC2 #2:**
```
MYSQL_ROOT_PASSWORD=...
POSTGRES_PASSWORD=...
```

**EC2 #1:**
```
DB_HOST=<ip-privada-ec2-2>
MYSQL_USER=... MYSQL_PASSWORD=... MYSQL_DB=ms1_usuarios
PG_USER=... PG_PASSWORD=... PG_DB=ms3_pedidos
MONGO_URI=mongodb://<ip-privada-ec2-2>:27017/ms2_catalogo
JWT_SECRET=...
AWS_ACCESS_KEY_ID=...        # para MS5
AWS_SECRET_ACCESS_KEY=...
ATHENA_DATABASE=ubereats_datalake
```
