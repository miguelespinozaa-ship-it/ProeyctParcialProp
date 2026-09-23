#!/usr/bin/env bash
# Configura las 2 App Tier: clona el repo, arma el .env con la IP de la BD y levanta los 5 MS + NGINX.
source "$(dirname "$0")/lib.sh"

configurar_app() {
  local id="$1" nombre="$2"
  echo "== Configurando $nombre ($id) =="
  ssm_run "$id" <<EOF
set -e
sudo -u ubuntu -H bash -c '
  [ -d ~/app ] || git clone $REPO_URL_HTTPS ~/app
  cd ~/app
  cp -n .env.example .env
  sed -i "s#^DB_HOST=.*#DB_HOST=$DB_IP#" .env
  sed -i "s#^MYSQL_DATABASE=.*#MYSQL_DATABASE=$MYSQL_DATABASE#" .env
  sed -i "s#^MYSQL_USER=.*#MYSQL_USER=$MYSQL_USER#" .env
  sed -i "s#^MYSQL_PASSWORD=.*#MYSQL_PASSWORD=$MYSQL_PASSWORD#" .env
  sed -i "s#^POSTGRES_DB=.*#POSTGRES_DB=$POSTGRES_DB#" .env
  sed -i "s#^POSTGRES_USER=.*#POSTGRES_USER=$POSTGRES_USER#" .env
  sed -i "s#^POSTGRES_PASSWORD=.*#POSTGRES_PASSWORD=$POSTGRES_PASSWORD#" .env
  sed -i "s#^JWT_SECRET=.*#JWT_SECRET=$JWT_SECRET#" .env
  grep -q "^NODE_NAME=" .env || echo "NODE_NAME=$nombre" >> .env
  docker compose -f docker-compose.app.yml up -d --build
'
EOF
}

configurar_app "$APP1" app-1
configurar_app "$APP2" app-2

echo "== Verificando MS1 en ambas =="
ssm_run "$APP1" <<'EOF'
for i in $(seq 1 20); do curl -sf localhost/ms1/health && break; sleep 5; done
EOF
ssm_run "$APP2" <<'EOF'
for i in $(seq 1 20); do curl -sf localhost/ms1/health && break; sleep 5; done
EOF

echo "App Tier lista en ambas instancias."
