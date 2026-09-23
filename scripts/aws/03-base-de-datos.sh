#!/usr/bin/env bash
# Configura PP-DB-Tier: clona el repo, genera credenciales, levanta las 3 BD y siembra MongoDB.
source "$(dirname "$0")/lib.sh"

# Genera credenciales propias una sola vez y las reusan los demas scripts.
: "${MYSQL_ROOT_PASSWORD:=$(openssl rand -hex 16)}"
: "${MYSQL_PASSWORD:=$(openssl rand -hex 16)}"
: "${POSTGRES_PASSWORD:=$(openssl rand -hex 16)}"
: "${JWT_SECRET:=$(openssl rand -hex 32)}"
guardar MYSQL_ROOT_PASSWORD "$MYSQL_ROOT_PASSWORD"
guardar MYSQL_PASSWORD "$MYSQL_PASSWORD"
guardar POSTGRES_PASSWORD "$POSTGRES_PASSWORD"
guardar JWT_SECRET "$JWT_SECRET"
guardar MYSQL_DATABASE "ms1_usuarios"
guardar MYSQL_USER "ms1_user"
guardar POSTGRES_DB "ms3_pedidos"
guardar POSTGRES_USER "ms3_user"

echo "== Configurando PP-DB-Tier =="
ssm_run "$DB" <<EOF
set -e
sudo -u ubuntu -H bash -c '
  [ -d ~/app ] || git clone $REPO_URL_HTTPS ~/app
  cd ~/app
  cp -n .env.example .env
  sed -i "s#^MYSQL_ROOT_PASSWORD=.*#MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD#" .env
  sed -i "s#^MYSQL_DATABASE=.*#MYSQL_DATABASE=$MYSQL_DATABASE#" .env
  sed -i "s#^MYSQL_USER=.*#MYSQL_USER=$MYSQL_USER#" .env
  sed -i "s#^MYSQL_PASSWORD=.*#MYSQL_PASSWORD=$MYSQL_PASSWORD#" .env
  sed -i "s#^POSTGRES_DB=.*#POSTGRES_DB=$POSTGRES_DB#" .env
  sed -i "s#^POSTGRES_USER=.*#POSTGRES_USER=$POSTGRES_USER#" .env
  sed -i "s#^POSTGRES_PASSWORD=.*#POSTGRES_PASSWORD=$POSTGRES_PASSWORD#" .env
  sed -i "s#^JWT_SECRET=.*#JWT_SECRET=$JWT_SECRET#" .env
  docker compose -f docker-compose.db.yml up -d --build
'
EOF

echo "== Sembrando MongoDB (20,000 restaurantes) =="
ssm_run "$DB" <<'EOF'
set -e
sudo -u ubuntu -H bash -c '
  cd ~/app
  for i in $(seq 1 20); do docker exec mongo mongosh --quiet --eval "db.runCommand({ping:1})" >/dev/null 2>&1 && break; sleep 5; done
  docker cp ms2-catalogo-restaurantes/seed.js mongo:/tmp/seed.js
  docker exec mongo mongosh --quiet --file /tmp/seed.js
'
EOF

echo "PP-DB-Tier lista."
