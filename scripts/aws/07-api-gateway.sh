#!/usr/bin/env bash
# API Gateway HTTPS publico, conectado al ALB interno por un VPC Link.
source "$(dirname "$0")/lib.sh"

VL=$(aws apigatewayv2 get-vpc-links --query "Items[?Name=='pp-vpclink'].VpcLinkId" --output text)
if [ -z "$VL" ]; then
  VL=$(aws apigatewayv2 create-vpc-link --name pp-vpclink --subnet-ids "$SUB_A" "$SUB_B" \
    --security-group-ids "$SG_VPCLINK" --query VpcLinkId --output text)
fi
guardar VL "$VL"

echo "Esperando a que el VPC Link este disponible (puede tardar varios minutos)..."
for _ in $(seq 1 40); do
  estado=$(aws apigatewayv2 get-vpc-link --vpc-link-id "$VL" --query VpcLinkStatus --output text)
  [ "$estado" = "AVAILABLE" ] && break
  sleep 15
done

API=$(aws apigatewayv2 get-apis --query "Items[?Name=='pp-api'].ApiId" --output text)
if [ -z "$API" ]; then
  API=$(aws apigatewayv2 create-api --name pp-api --protocol-type HTTP \
    --cors-configuration AllowOrigins="*",AllowMethods="*",AllowHeaders="*",ExposeHeaders="X-Total-Count" \
    --query ApiId --output text)
fi
guardar API "$API"

INT=$(aws apigatewayv2 get-integrations --api-id "$API" --query 'Items[0].IntegrationId' --output text 2>/dev/null)
if [ "$INT" = "None" ] || [ -z "$INT" ]; then
  INT=$(aws apigatewayv2 create-integration --api-id "$API" --integration-type HTTP_PROXY --integration-method ANY \
    --integration-uri "$LST" --connection-type VPC_LINK --connection-id "$VL" --payload-format-version 1.0 \
    --timeout-in-millis 29000 --query IntegrationId --output text)
  aws apigatewayv2 create-route --api-id "$API" --route-key '$default' --target "integrations/$INT" >/dev/null
  aws apigatewayv2 create-stage --api-id "$API" --stage-name '$default' --auto-deploy >/dev/null
fi

GATEWAY_URL="https://$API.execute-api.$REGION.amazonaws.com"
guardar GATEWAY_URL "$GATEWAY_URL"
echo "API Gateway: $GATEWAY_URL"

echo "Probando..."
for _ in $(seq 1 10); do
  curl -sf "$GATEWAY_URL/ms1/health" >/dev/null && { echo "ms1 OK"; break; }
  sleep 10
done
