#!/usr/bin/env bash
# Carga masiva (>=20,000 registros por base) y enlace del admin demo con un restaurante real.
source "$(dirname "$0")/lib.sh"

echo "== Usuarios (MySQL) y pedidos (PostgreSQL), desde PP-App-Tier =="
ssm_run "$APP1" <<'EOF'
set -e
docker exec ms1 python seed.py
docker exec ms3 node seed.js
EOF

echo "== Enlazando el restaurante del admin demo =="
RID=$(ssm_run "$APP1" <<'EOF'
curl -s "localhost/ms2/api/v1/restaurants?page=1&page_size=1" | python3 -c "import sys,json;print(json.load(sys.stdin)['items'][0]['id'])"
EOF
)
RID=$(echo "$RID" | tail -1 | tr -d '\r')
echo "Restaurante: $RID"

ssm_run "$DB" <<EOF
docker exec mysql mysql -u$MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE \
  -e "UPDATE usuarios SET restaurante_id='$RID' WHERE email='admin@demo.com';"
EOF

echo "Carga masiva completa."
