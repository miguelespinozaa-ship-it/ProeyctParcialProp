#!/usr/bin/env bash
# Apaga o elimina todo lo creado por estos scripts.
# Uso: ./99-destruir.sh pausar   -> detiene las EC2, conserva todo (para seguir despues)
#      ./99-destruir.sh borrar   -> elimina EC2, ALB, API Gateway, VPC Link, Amplify y el bucket S3
source "$(dirname "$0")/lib.sh"

MODO="${1:-}"
if [ "$MODO" != "pausar" ] && [ "$MODO" != "borrar" ]; then
  echo "Uso: $0 pausar|borrar" >&2
  exit 1
fi

IDS=""
for v in DB APP1 APP2 INGEST; do
  [ -n "${!v:-}" ] && IDS="$IDS ${!v}"
done

if [ "$MODO" = "pausar" ]; then
  if [ -n "$IDS" ]; then
    aws ec2 stop-instances --instance-ids $IDS
  fi
  echo "Instancias detenidas. Los discos y los datos se conservan."
  exit 0
fi

echo "Borrando todo. Esto no se puede deshacer."
[ -n "${ALB:-}" ] && { aws elbv2 delete-load-balancer --load-balancer-arn "$ALB" 2>/dev/null || true; }
[ -n "${API:-}" ] && { aws apigatewayv2 delete-api --api-id "$API" 2>/dev/null || true; }
[ -n "${VL:-}" ] && { aws apigatewayv2 delete-vpc-link --vpc-link-id "$VL" 2>/dev/null || true; }
[ -n "${AMPLIFY_APP_ID:-}" ] && { aws amplify delete-app --app-id "$AMPLIFY_APP_ID" 2>/dev/null || true; }
if [ -n "$IDS" ]; then
  aws ec2 terminate-instances --instance-ids $IDS
fi
[ -n "${BUCKET:-}" ] && { aws s3 rb "s3://$BUCKET" --force 2>/dev/null || true; }
echo "Listo."
