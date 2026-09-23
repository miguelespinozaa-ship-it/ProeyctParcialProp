#!/usr/bin/env bash
# Balanceador de carga interno (ALB) entre las 2 App Tier.
source "$(dirname "$0")/lib.sh"

ALB=$(aws elbv2 describe-load-balancers --names pp-alb-interno --query 'LoadBalancers[0].LoadBalancerArn' --output text 2>/dev/null || true)
if [ "$ALB" = "None" ] || [ -z "$ALB" ]; then
  ALB=$(aws elbv2 create-load-balancer --name pp-alb-interno --scheme internal --type application \
    --subnets "$SUB_A" "$SUB_B" --security-groups "$SG_ALB" --query 'LoadBalancers[0].LoadBalancerArn' --output text)
fi
guardar ALB "$ALB"

TG=$(aws elbv2 describe-target-groups --names pp-app-tg --query 'TargetGroups[0].TargetGroupArn' --output text 2>/dev/null || true)
if [ "$TG" = "None" ] || [ -z "$TG" ]; then
  TG=$(aws elbv2 create-target-group --name pp-app-tg --protocol HTTP --port 80 --vpc-id "$VPC" \
    --target-type instance --health-check-path /health --health-check-interval-seconds 15 \
    --healthy-threshold-count 2 --unhealthy-threshold-count 2 --query 'TargetGroups[0].TargetGroupArn' --output text)
fi
guardar TG "$TG"

aws elbv2 register-targets --target-group-arn "$TG" --targets Id="$APP1" Id="$APP2" >/dev/null

LST=$(aws elbv2 describe-listeners --load-balancer-arn "$ALB" --query 'Listeners[0].ListenerArn' --output text 2>/dev/null)
if [ "$LST" = "None" ] || [ -z "$LST" ]; then
  LST=$(aws elbv2 create-listener --load-balancer-arn "$ALB" --protocol HTTP --port 80 \
    --default-actions Type=forward,TargetGroupArn="$TG" --query 'Listeners[0].ListenerArn' --output text)
fi
guardar LST "$LST"

echo "Esperando a que el ALB este disponible..."
aws elbv2 wait load-balancer-available --load-balancer-arns "$ALB"

echo "Esperando a que las 2 instancias esten healthy..."
for _ in $(seq 1 20); do
  n=$(aws elbv2 describe-target-health --target-group-arn "$TG" \
    --query 'length(TargetHealthDescriptions[?TargetHealth.State==`healthy`])' --output text)
  [ "$n" = "2" ] && break
  sleep 15
done
aws elbv2 describe-target-health --target-group-arn "$TG" \
  --query 'TargetHealthDescriptions[].[Target.Id,TargetHealth.State]' --output text

echo "ALB=$ALB"
