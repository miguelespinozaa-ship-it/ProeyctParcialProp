#!/usr/bin/env bash
# Corre los 10 pasos en orden. Requiere `aws configure` ya hecho con permisos de
# EC2, IAM, ELB, API Gateway, Amplify, S3, Glue y Athena.
# Uso: ./desplegar-todo.sh
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for paso in 01-red 02-instancias 03-base-de-datos 04-app-tier 05-carga-masiva \
            06-balanceador 07-api-gateway 08-datalake 09-amplify 10-verificar; do
  echo ""
  echo "############################################################"
  echo "# $paso"
  echo "############################################################"
  bash "$DIR/$paso.sh"
done

echo ""
echo "Despliegue completo. Para pausar o borrar: ./99-destruir.sh pausar|borrar"
