# Despliegue en AWS (cuenta propia)

Guía para desplegar este proyecto en una cuenta de AWS estándar (no Learner Lab). Reproduce la arquitectura
descrita en [`microservicios/00-mapa-conexiones.md`](microservicios/00-mapa-conexiones.md) y en el informe
técnico: 4 EC2 (2 de App balanceadas + 1 de BD privada + 1 de Ingesta), un ALB interno, API Gateway con
HTTPS, AWS Amplify para el frontend, y S3 + Glue + Athena para la analítica.

Región usada en los ejemplos: `us-east-1`. Todos los comandos son AWS CLI (`aws configure` con un usuario
IAM que tenga permisos de EC2, IAM, ELB, API Gateway, Amplify, S3, Glue y Athena); las variables `$...`
hay que reemplazarlas por los IDs reales que devuelve cada comando.

**Costo:** son 4 instancias `t3.micro` + un Application Load Balancer (el ALB cobra por hora aunque no
reciba tráfico). Fuera del Free Tier son pocos dólares por día. Sección final: cómo apagarlo todo.

**Automatizado:** [`scripts/aws/`](scripts/aws/) tiene un script en bash por cada paso de esta guía y un
orquestador (`desplegar-todo.sh`) que los corre todos en orden. Esta guía explica cada paso; los scripts
lo ejecutan.

## 0. Prerrequisitos

```bash
aws sts get-caller-identity          # confirma que las credenciales están activas
VPC=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)
SUBNETS=$(aws ec2 describe-subnets --filters Name=vpc-id,Values=$VPC --query 'Subnets[].SubnetId' --output text)
echo $VPC $SUBNETS                   # se necesita el VPC por defecto y al menos 2 subredes en 2 AZs distintas
SUB_A=$(echo $SUBNETS | awk '{print $1}')
SUB_B=$(echo $SUBNETS | awk '{print $2}')
```

## 1. Rol IAM para las EC2

Las instancias necesitan permiso para SSM (administrarlas sin SSH) y, la de ingesta, para S3/Glue/Athena.

```bash
aws iam create-role --role-name pp-ec2-role --assume-role-policy-document '{
  "Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
aws iam attach-role-policy --role-name pp-ec2-role --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
aws iam attach-role-policy --role-name pp-ec2-role --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
aws iam attach-role-policy --role-name pp-ec2-role --policy-arn arn:aws:iam::aws:policy/AmazonAthenaFullAccess
aws iam attach-role-policy --role-name pp-ec2-role --policy-arn arn:aws:iam::aws:policy/AWSGlueConsoleFullAccess
aws iam create-instance-profile --instance-profile-name pp-ec2-role
aws iam add-role-to-instance-profile --instance-profile-name pp-ec2-role --role-name pp-ec2-role
sleep 15   # IAM tarda unos segundos en propagar
```

## 2. Security groups

```bash
SG_APP=$(aws ec2 create-security-group --group-name pp-app-tier-sg --description "App Tier" --vpc-id $VPC --query GroupId --output text)
SG_DB=$(aws ec2 create-security-group --group-name pp-db-tier-sg --description "DB Tier, privada" --vpc-id $VPC --query GroupId --output text)
SG_INGEST=$(aws ec2 create-security-group --group-name pp-ingest-sg --description "Ingesta, sin entradas" --vpc-id $VPC --query GroupId --output text)
SG_ALB=$(aws ec2 create-security-group --group-name pp-alb-sg --description "ALB interno" --vpc-id $VPC --query GroupId --output text)
SG_VPCLINK=$(aws ec2 create-security-group --group-name pp-vpclink-sg --description "VPC Link de API Gateway" --vpc-id $VPC --query GroupId --output text)

# El ALB solo acepta tráfico del VPC Link; las App Tier solo del ALB; la BD solo de App e Ingesta.
aws ec2 authorize-security-group-ingress --group-id $SG_ALB --protocol tcp --port 80 --source-group $SG_VPCLINK
aws ec2 authorize-security-group-ingress --group-id $SG_APP --protocol tcp --port 80 --source-group $SG_ALB
aws ec2 authorize-security-group-ingress --group-id $SG_DB --protocol tcp --port 3306 --source-group $SG_APP
aws ec2 authorize-security-group-ingress --group-id $SG_DB --protocol tcp --port 5432 --source-group $SG_APP
aws ec2 authorize-security-group-ingress --group-id $SG_DB --protocol tcp --port 27017 --source-group $SG_APP
aws ec2 authorize-security-group-ingress --group-id $SG_DB --protocol tcp --port 3306 --source-group $SG_INGEST
aws ec2 authorize-security-group-ingress --group-id $SG_DB --protocol tcp --port 5432 --source-group $SG_INGEST
aws ec2 authorize-security-group-ingress --group-id $SG_DB --protocol tcp --port 27017 --source-group $SG_INGEST
```

## 3. Lanzar las 4 EC2

AMI: Ubuntu Server 22.04 LTS del catálogo público (`ami-0e2c8caa4b6378d8c` en `us-east-1`; si es otra región,
buscar "Ubuntu Server 22.04" en el AMI Catalog de la consola). `user-data` instala Docker solo.

```bash
AMI=ami-0e2c8caa4b6378d8c   # verificar el ID vigente en el AMI Catalog si cambió
USERDATA='#!/bin/bash
curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu'
UD_B64=$(echo "$USERDATA" | base64 -w0)

DB=$(aws ec2 run-instances --image-id $AMI --instance-type t3.micro --subnet-id $SUB_A \
  --security-group-ids $SG_DB --iam-instance-profile Name=pp-ec2-role --user-data "$UD_B64" \
  --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=20}' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=PP-DB-Tier}]' --query 'Instances[0].InstanceId' --output text)

APP1=$(aws ec2 run-instances --image-id $AMI --instance-type t3.micro --subnet-id $SUB_A \
  --security-group-ids $SG_APP --iam-instance-profile Name=pp-ec2-role --user-data "$UD_B64" --associate-public-ip-address \
  --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=20}' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=PP-App-Tier}]' --query 'Instances[0].InstanceId' --output text)

APP2=$(aws ec2 run-instances --image-id $AMI --instance-type t3.micro --subnet-id $SUB_B \
  --security-group-ids $SG_APP --iam-instance-profile Name=pp-ec2-role --user-data "$UD_B64" --associate-public-ip-address \
  --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=20}' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=PP-App-Tier-2}]' --query 'Instances[0].InstanceId' --output text)

INGEST=$(aws ec2 run-instances --image-id $AMI --instance-type t3.micro --subnet-id $SUB_A \
  --security-group-ids $SG_INGEST --iam-instance-profile Name=pp-ec2-role --user-data "$UD_B64" \
  --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=20}' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=PP-Ingest-VM}]' --query 'Instances[0].InstanceId' --output text)

aws ec2 wait instance-running --instance-ids $DB $APP1 $APP2 $INGEST
DB_IP=$(aws ec2 describe-instances --instance-ids $DB --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)
echo "DB privada: $DB_IP"
```

Conectarse sin SSH, desde la consola de EC2: seleccionar la instancia → **Connect → Session Manager → Connect**
(funciona apenas SSM confirma el agente, 1-2 minutos después del `run-instances`).

## 4. Base de datos (PP-DB-Tier)

Conectado por Session Manager a la instancia `PP-DB-Tier`:

```bash
sudo su - ubuntu
git clone https://github.com/miguelespinozaa-ship-it/ProeyctParcialProp.git app && cd app
cp .env.example .env
nano .env   # poner contraseñas propias en MYSQL_*/POSTGRES_* y un JWT_SECRET de 32+ bytes propio
docker compose -f docker-compose.db.yml up -d --build
```

Los seeds de MySQL y PostgreSQL se disparan desde los contenedores `ms1`/`ms3` (paso 5, porque ahí vive el
código); el de MongoDB corre directo acá, contra el contenedor `mongo` de esta misma instancia:

```bash
docker cp ms2-catalogo-restaurantes/seed.js mongo:/tmp/seed.js
docker exec mongo mongosh --quiet --file /tmp/seed.js   # 20,000 restaurantes
```

## 5. App Tier (repetir en PP-App-Tier y PP-App-Tier-2)

```bash
sudo su - ubuntu
git clone https://github.com/miguelespinozaa-ship-it/ProeyctParcialProp.git app && cd app
cp .env.example .env
nano .env
# DB_HOST=<IP privada de PP-DB-Tier>
# MYSQL_*/POSTGRES_* = las MISMAS contraseñas que pusiste en el paso 4
# JWT_SECRET = el MISMO valor en las dos App Tier y en la BD
echo "NODE_NAME=app-1" >> .env    # en la segunda instancia: NODE_NAME=app-2
docker compose -f docker-compose.app.yml up -d --build
curl localhost/ms1/health         # debe responder {"status":"ok",...}
```

Carga masiva (solo en `PP-App-Tier`, una sola vez — el contenedor llega a la BD por `DB_HOST`):

```bash
docker exec ms1 python seed.py        # ≥20,000 usuarios (MySQL)
docker exec ms3 node seed.js          # ≥20,000 pedidos (PostgreSQL)
```

Paso único: enlazar el restaurante del admin demo. El `_id` de Mongo se pide desde la App Tier (donde
responde MS2), pero el `UPDATE` corre en `PP-DB-Tier` (ahí vive el contenedor `mysql`):

```bash
# en PP-App-Tier:
curl -s "localhost/ms2/api/v1/restaurants?page=1&page_size=1" | python3 -c "import sys,json;print(json.load(sys.stdin)['items'][0]['id'])"
```
```bash
# en PP-DB-Tier, con el _id de arriba:
docker exec mysql mysql -u$MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE \
  -e "UPDATE usuarios SET restaurante_id='<_id de arriba>' WHERE email='admin@demo.com';"
```

## 6. Balanceador de carga interno (ALB)

```bash
ALB=$(aws elbv2 create-load-balancer --name pp-alb-interno --scheme internal --type application \
  --subnets $SUB_A $SUB_B --security-groups $SG_ALB --query 'LoadBalancers[0].LoadBalancerArn' --output text)
TG=$(aws elbv2 create-target-group --name pp-app-tg --protocol HTTP --port 80 --vpc-id $VPC \
  --target-type instance --health-check-path /health --health-check-interval-seconds 15 \
  --healthy-threshold-count 2 --unhealthy-threshold-count 2 --query 'TargetGroups[0].TargetGroupArn' --output text)
aws elbv2 register-targets --target-group-arn $TG --targets Id=$APP1 Id=$APP2
LST=$(aws elbv2 create-listener --load-balancer-arn $ALB --protocol HTTP --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG --query 'Listeners[0].ListenerArn' --output text)
aws elbv2 wait load-balancer-available --load-balancer-arns $ALB
aws elbv2 describe-target-health --target-group-arn $TG --query 'TargetHealthDescriptions[].[Target.Id,TargetHealth.State]' --output text
```

## 7. API Gateway (HTTPS público → VPC Link → ALB)

```bash
VL=$(aws apigatewayv2 create-vpc-link --name pp-vpclink --subnet-ids $SUB_A $SUB_B \
  --security-group-ids $SG_VPCLINK --query VpcLinkId --output text)
until [ "$(aws apigatewayv2 get-vpc-link --vpc-link-id $VL --query VpcLinkStatus --output text)" = AVAILABLE ]; do sleep 15; done

API=$(aws apigatewayv2 create-api --name pp-api --protocol-type HTTP \
  --cors-configuration AllowOrigins="*",AllowMethods="*",AllowHeaders="*",ExposeHeaders="X-Total-Count" \
  --query ApiId --output text)
INT=$(aws apigatewayv2 create-integration --api-id $API --integration-type HTTP_PROXY --integration-method ANY \
  --integration-uri $LST --connection-type VPC_LINK --connection-id $VL --payload-format-version 1.0 \
  --timeout-in-millis 29000 --query IntegrationId --output text)
aws apigatewayv2 create-route --api-id $API --route-key '$default' --target integrations/$INT
aws apigatewayv2 create-stage --api-id $API --stage-name '$default' --auto-deploy

echo "https://$API.execute-api.us-east-1.amazonaws.com"
curl https://$API.execute-api.us-east-1.amazonaws.com/ms1/health
```

## 8. Frontend en AWS Amplify (con CI/CD)

1. Consola → **AWS Amplify → Create new app → GitHub** → autorizar y elegir el repositorio (público, no
   hace falta fork) y la rama `main`.
2. Marcar **My app is a monorepo**, carpeta raíz `frontend`. Amplify detecta [`amplify.yml`](amplify.yml)
   solo (usa Node 22, `npm ci`, `npm run build`, artefactos en `dist`).
3. En **Variables de entorno** agregar `VITE_API_BASE_URL` = la URL de API Gateway del paso 7.
4. Guardar y desplegar (2-3 min). Después, en **Rewrites and redirects**, agregar la regla `/<*>` →
   `/index.html`, tipo **200 (Rewrite)** (necesaria para que las rutas de React Router no den 404 al recargar).
5. Cada `git push` a `main` vuelve a compilar y desplegar solo.

## 9. Data lake: S3 + ingesta + Glue + Athena

```bash
BUCKET=tu-nombre-unico-ubereats-datalake   # el nombre de bucket es global en todo S3
aws s3 mb s3://$BUCKET
```

En `PP-Ingest-VM` (conectado por Session Manager):
```bash
sudo su - ubuntu
git clone https://github.com/miguelespinozaa-ship-it/ProeyctParcialProp.git app && cd app/data-science
cp .env.example .env
nano .env   # DB_HOST=<IP privada de PP-DB-Tier>, MYSQL_*/POSTGRES_* iguales al paso 4, S3_BUCKET=el de arriba
docker compose -f docker-compose.ingest.yml up --build   # sube usuarios/direcciones/orders/order_items/restaurantes a S3
```

Glue (catálogo) y Athena (consultas):
```bash
aws glue create-database --database-input Name=ubereats_datalake
ROLE_GLUE=$(aws iam get-role --role-name pp-ec2-role --query Role.Arn --output text)   # reusa el mismo rol
aws glue create-crawler --name pp-crawler --role $ROLE_GLUE --database-name ubereats_datalake \
  --targets S3Targets="[{Path=s3://$BUCKET/raw/}]"
aws glue start-crawler --name pp-crawler
aws athena create-work-group --name pp-workgroup --configuration \
  ResultConfiguration="{OutputLocation=s3://$BUCKET/athena-results/}"
```
Esperar 1-2 minutos y correr en la consola de Athena (workgroup `pp-workgroup`, base `ubereats_datalake`)
el contenido de [`data-science/athena/queries_and_views.sql`](data-science/athena/queries_and_views.sql),
sentencia por sentencia (crea las vistas `v_resumen_ventas_restaurante` y `v_metricas_usuarios`).

Conectar MS5 a Athena real: en **ambas** App Tier, editar `.env` → `ATHENA_MOCK=false`,
`ATHENA_DATABASE=ubereats_datalake`, `ATHENA_OUTPUT_S3=s3://$BUCKET/athena-results/`, y
`docker compose -f docker-compose.app.yml up -d --build ms5`.

## 10. Verificación

```bash
GW=https://$API.execute-api.us-east-1.amazonaws.com
for p in ms1 ms2 ms3 ms4 ms5; do curl -s -o /dev/null -w "$p %{http_code}\n" $GW/$p/health; done
npx newman run postman/delivery-cloud.postman_collection.json --env-var "base_url=$GW"
```
Y en el navegador: la URL de Amplify, login con `customer@demo.com` / `admin@demo.com` / `delivery@demo.com`
(clave `password123`).

## 11. Apagar / eliminar (para no seguir pagando)

```bash
aws ec2 stop-instances --instance-ids $DB $APP1 $APP2 $INGEST     # pausa (conserva discos y datos)
# borrado completo cuando ya no se necesite:
aws elbv2 delete-load-balancer --load-balancer-arn $ALB
aws apigatewayv2 delete-api --api-id $API
aws apigatewayv2 delete-vpc-link --vpc-link-id $VL
aws ec2 terminate-instances --instance-ids $DB $APP1 $APP2 $INGEST
aws s3 rb s3://$BUCKET --force
```
