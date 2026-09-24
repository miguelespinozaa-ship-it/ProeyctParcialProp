#!/usr/bin/env bash
# Data lake: bucket S3, ingesta, Glue Crawler, Athena (workgroup, 4 queries y 2 vistas).
source "$(dirname "$0")/lib.sh"

ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
BUCKET="pp-ubereats-datalake-$ACCOUNT"
guardar BUCKET "$BUCKET"

echo "== Bucket S3: $BUCKET =="
aws s3 mb "s3://$BUCKET" --region "$REGION" 2>/dev/null || echo "Ya existe."

echo "== Configurando la ingesta en PP-Ingest-VM =="
ssm_run "$INGEST" <<EOF
set -e
sudo -u ubuntu -H bash -c '
  [ -d ~/app ] || git clone $REPO_URL_HTTPS ~/app
  cd ~/app/data-science
  cp -n .env.example .env
  sed -i "s#^DB_HOST=.*#DB_HOST=$DB_IP#" .env
  sed -i "s#^MYSQL_USER=.*#MYSQL_USER=$MYSQL_USER#" .env
  sed -i "s#^MYSQL_PASSWORD=.*#MYSQL_PASSWORD=$MYSQL_PASSWORD#" .env
  sed -i "s#^MYSQL_DATABASE=.*#MYSQL_DATABASE=$MYSQL_DATABASE#" .env
  sed -i "s#^POSTGRES_USER=.*#POSTGRES_USER=$POSTGRES_USER#" .env
  sed -i "s#^POSTGRES_PASSWORD=.*#POSTGRES_PASSWORD=$POSTGRES_PASSWORD#" .env
  sed -i "s#^POSTGRES_DB=.*#POSTGRES_DB=$POSTGRES_DB#" .env
  sed -i "s#^S3_BUCKET=.*#S3_BUCKET=$BUCKET#" .env
  grep -q "^S3_BUCKET=" .env || echo "S3_BUCKET=$BUCKET" >> .env
  docker compose -f docker-compose.ingest.yml up --build
'
EOF

echo "== Glue: base de datos y crawler =="
aws glue create-database --database-input Name=ubereats_datalake 2>/dev/null || echo "Base ya existe."
ROL_GLUE_NOMBRE="${PERFIL_EC2/LabInstanceProfile/LabRole}"
ROLE_GLUE=$(aws iam get-role --role-name "$ROL_GLUE_NOMBRE" --query Role.Arn --output text)
aws glue create-crawler --name pp-crawler --role "$ROLE_GLUE" --database-name ubereats_datalake \
  --targets S3Targets="[{Path=s3://$BUCKET/raw/}]" 2>/dev/null || echo "Crawler ya existe."
aws glue start-crawler --name pp-crawler
echo "Esperando al crawler..."
for _ in $(seq 1 30); do
  estado=$(aws glue get-crawler --name pp-crawler --query Crawler.State --output text)
  [ "$estado" = "READY" ] && break
  sleep 15
done

echo "== Athena: workgroup =="
aws athena create-work-group --name pp-workgroup --configuration \
  ResultConfiguration="{OutputLocation=s3://$BUCKET/athena-results/}" 2>/dev/null || echo "Workgroup ya existe."

echo "== Athena: 4 consultas + 2 vistas =="
STMTS_FILE=$(mktemp)
python3 - "$DIR/../../data-science/athena/queries_and_views.sql" > "$STMTS_FILE" << 'PYEOF'
import sys
sql = open(sys.argv[1]).read()
for stmt in sql.split(";"):
    stmt = stmt.strip()
    if stmt and not stmt.startswith("--"):
        sys.stdout.write(stmt.replace("\n", " ") + ";\0")
PYEOF

n=0
while IFS= read -r -d '' stmt; do
  n=$((n + 1))
  echo "Consulta $n..."
  qid=$(aws athena start-query-execution --work-group pp-workgroup \
    --query-execution-context Database=ubereats_datalake --query-string "$stmt" \
    --query QueryExecutionId --output text)
  for _ in $(seq 1 30); do
    estado=$(aws athena get-query-execution --query-execution-id "$qid" --query 'QueryExecution.Status.State' --output text)
    [ "$estado" = "SUCCEEDED" ] || [ "$estado" = "FAILED" ] && break
    sleep 2
  done
  if [ "$estado" != "SUCCEEDED" ]; then
    echo "Fallo la consulta $n ($estado):" >&2
    aws athena get-query-execution --query-execution-id "$qid" --query 'QueryExecution.Status.StateChangeReason' --output text >&2
    exit 1
  fi
done < "$STMTS_FILE"
rm -f "$STMTS_FILE"
echo "$n sentencias ejecutadas (4 consultas + 2 CREATE VIEW)."

echo "== Conectando MS5 a Athena real =="
for id in "$APP1" "$APP2"; do
  ssm_run "$id" <<EOF
set -e
sudo -u ubuntu -H bash -c '
  cd ~/app
  sed -i "s#^ATHENA_MOCK=.*#ATHENA_MOCK=false#" .env
  sed -i "s#^ATHENA_DATABASE=.*#ATHENA_DATABASE=ubereats_datalake#" .env
  sed -i "s#^ATHENA_OUTPUT_S3=.*#ATHENA_OUTPUT_S3=s3://$BUCKET/athena-results/#" .env
  docker compose -f docker-compose.app.yml up -d --build ms5
'
EOF
done
