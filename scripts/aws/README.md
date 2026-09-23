# Scripts de despliegue automatizado en AWS

Automatizan paso a paso lo mismo que [`DESPLIEGUE-AWS.md`](../../DESPLIEGUE-AWS.md) en la raíz del
repositorio: las 4 EC2, el balanceador de carga interno, el API Gateway, el frontend en Amplify y el
data lake (S3 + Glue + Athena). Usar la guía en markdown para entender cada paso; estos scripts sirven
para ejecutarlo sin copiar y pegar comando por comando.

## Requisitos

- AWS CLI configurado (`aws configure`) con un usuario IAM con permisos de EC2, IAM, ELB, API Gateway,
  Amplify, S3, Glue y Athena.
- `python3`, `openssl` y `curl` instalados (para generar contraseñas y armar los parámetros de SSM).
- Opcional: `npx` (Node.js) para correr la colección de Postman en el paso de verificación.

## Uso

```bash
cd scripts/aws
./desplegar-todo.sh
```

Tarda entre 20 y 40 minutos (la mayor parte esperando a que arranquen las instancias, el ALB, el VPC
Link y el crawler de Glue). Al final imprime la URL del API Gateway y, si Amplify quedó conectado a
GitHub, la URL del frontend.

También se puede correr paso a paso, en este orden:

| Script | Qué hace |
|---|---|
| `01-red.sh` | Rol IAM de las EC2 y los 5 security groups |
| `02-instancias.sh` | Lanza las 4 EC2 (Ubuntu 22.04 + Docker) |
| `03-base-de-datos.sh` | Configura la BD y siembra MongoDB (20,000 restaurantes) |
| `04-app-tier.sh` | Configura las 2 App Tier y levanta los 5 microservicios |
| `05-carga-masiva.sh` | Siembra MySQL y PostgreSQL, enlaza el admin demo |
| `06-balanceador.sh` | ALB interno + target group |
| `07-api-gateway.sh` | VPC Link + API Gateway (HTTPS) |
| `08-datalake.sh` | Ingesta, Glue Crawler, Athena (4 consultas + 2 vistas), conecta MS5 |
| `09-amplify.sh` | Frontend en Amplify (ver abajo el caso de GitHub) |
| `10-verificar.sh` | Health checks + colección de Postman |
| `99-destruir.sh` | `pausar` (detiene las EC2) o `borrar` (elimina todo) |

Cada script guarda los IDs que crea en `state.env` (no se sube al repo) y los siguientes scripts los
reusan. Se pueden volver a correr sin duplicar recursos: cada uno revisa primero si el recurso ya existe.

## Amplify y GitHub

Conectar Amplify a un repositorio de GitHub requiere autorizar por OAuth en el navegador, algo que no se
puede automatizar sin un token. Dos opciones:

- **Con token:** generar un token personal de GitHub (permiso `repo`) y correr
  `GITHUB_TOKEN=<token> ./09-amplify.sh` — conecta el repositorio y queda con CI/CD (cada push a `main`
  se despliega solo).
- **Sin token:** `09-amplify.sh` crea la app y muestra los 3 pasos para conectarla a mano desde la
  consola.

## Apagar o borrar

```bash
./99-destruir.sh pausar   # detiene las 4 EC2, conserva discos y datos
./99-destruir.sh borrar   # elimina EC2, ALB, API Gateway, VPC Link, Amplify y el bucket S3
```
