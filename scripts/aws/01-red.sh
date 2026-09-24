#!/usr/bin/env bash
# Crea el rol IAM de las EC2 y los 5 security groups. Correr una sola vez.
source "$(dirname "$0")/lib.sh"

echo "== Rol IAM =="
PERFIL_EC2="pp-ec2-role"
if aws iam get-role --role-name pp-ec2-role >/dev/null 2>&1; then
  echo "Ya existe, se reusa."
else
  set +e
  SALIDA=$(aws iam create-role --role-name pp-ec2-role --assume-role-policy-document '{
    "Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}' 2>&1)
  RC=$?
  set -e
  if [ $RC -eq 0 ]; then
    aws iam attach-role-policy --role-name pp-ec2-role --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
    aws iam attach-role-policy --role-name pp-ec2-role --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
    aws iam attach-role-policy --role-name pp-ec2-role --policy-arn arn:aws:iam::aws:policy/AmazonAthenaFullAccess
    aws iam attach-role-policy --role-name pp-ec2-role --policy-arn arn:aws:iam::aws:policy/AWSGlueConsoleFullAccess
    aws iam create-instance-profile --instance-profile-name pp-ec2-role >/dev/null
    aws iam add-role-to-instance-profile --instance-profile-name pp-ec2-role --role-name pp-ec2-role
    echo "Creado. Esperando propagacion de IAM..."
    sleep 20
  elif echo "$SALIDA" | grep -q "AccessDenied"; then
    echo "Cuenta sin permiso para crear roles IAM (AWS Academy Learner Lab). Se usa LabInstanceProfile."
    PERFIL_EC2="LabInstanceProfile"
  else
    echo "$SALIDA" >&2
    exit 1
  fi
fi
guardar PERFIL_EC2 "$PERFIL_EC2"

echo "== VPC y subredes =="
VPC=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)
SUBNETS=$(aws ec2 describe-subnets --filters Name=vpc-id,Values="$VPC" --query 'Subnets[].SubnetId' --output text)
SUB_A=$(echo "$SUBNETS" | awk '{print $1}')
SUB_B=$(echo "$SUBNETS" | awk '{print $2}')
guardar VPC "$VPC"
guardar SUB_A "$SUB_A"
guardar SUB_B "$SUB_B"
echo "VPC=$VPC SUB_A=$SUB_A SUB_B=$SUB_B"

crear_sg() {
  local nombre="$1" desc="$2"
  local id
  id=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$nombre" "Name=vpc-id,Values=$VPC" \
    --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null)
  if [ "$id" = "None" ] || [ -z "$id" ]; then
    id=$(aws ec2 create-security-group --group-name "$nombre" --description "$desc" --vpc-id "$VPC" --query GroupId --output text)
  fi
  echo "$id"
}

echo "== Security groups =="
SG_APP=$(crear_sg pp-app-tier-sg "App Tier")
SG_DB=$(crear_sg pp-db-tier-sg "DB Tier, privada")
SG_INGEST=$(crear_sg pp-ingest-sg "Ingesta, sin entradas")
SG_ALB=$(crear_sg pp-alb-sg "ALB interno")
SG_VPCLINK=$(crear_sg pp-vpclink-sg "VPC Link de API Gateway")
guardar SG_APP "$SG_APP"
guardar SG_DB "$SG_DB"
guardar SG_INGEST "$SG_INGEST"
guardar SG_ALB "$SG_ALB"
guardar SG_VPCLINK "$SG_VPCLINK"

autorizar() {
  aws ec2 authorize-security-group-ingress --group-id "$1" --protocol tcp --port "$2" --source-group "$3" >/dev/null 2>&1 || true
}
autorizar "$SG_ALB" 80 "$SG_VPCLINK"
autorizar "$SG_APP" 80 "$SG_ALB"
autorizar "$SG_DB" 3306 "$SG_APP"
autorizar "$SG_DB" 5432 "$SG_APP"
autorizar "$SG_DB" 27017 "$SG_APP"
autorizar "$SG_DB" 3306 "$SG_INGEST"
autorizar "$SG_DB" 5432 "$SG_INGEST"
autorizar "$SG_DB" 27017 "$SG_INGEST"

echo "Listo: SG_APP=$SG_APP SG_DB=$SG_DB SG_INGEST=$SG_INGEST SG_ALB=$SG_ALB SG_VPCLINK=$SG_VPCLINK"
