#!/usr/bin/env bash
# Prueba los 5 microservicios a traves del API Gateway y corre la coleccion de Postman.
source "$(dirname "$0")/lib.sh"

echo "Gateway: $GATEWAY_URL"
for ms in ms1 ms2 ms3 ms4 ms5; do
  codigo=$(curl -s -o /dev/null -w "%{http_code}" --max-time 20 "$GATEWAY_URL/$ms/health")
  echo "$ms: $codigo"
done

if command -v npx >/dev/null; then
  npx --yes newman run "$DIR/../../postman/delivery-cloud.postman_collection.json" \
    --env-var "base_url=$GATEWAY_URL" --timeout-request 90000
else
  echo "npx no esta instalado; instalar Node.js para correr la coleccion de Postman."
fi
