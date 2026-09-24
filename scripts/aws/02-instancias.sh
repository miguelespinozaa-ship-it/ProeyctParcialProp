#!/usr/bin/env bash
# Lanza las 4 EC2 (BD, 2 de App, Ingesta) con Docker instalado por user-data.
source "$(dirname "$0")/lib.sh"
PERFIL_EC2="${PERFIL_EC2:-pp-ec2-role}"

AMI=$(ami_ubuntu_22_04)
echo "AMI: $AMI"

USERDATA='#!/bin/bash
curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu'

lanzar() {
  local nombre="$1" subred="$2" sg="$3" publica="$4"
  local extra=()
  [ "$publica" = "si" ] && extra=(--associate-public-ip-address)
  aws ec2 run-instances --image-id "$AMI" --instance-type t3.micro --subnet-id "$subred" \
    --security-group-ids "$sg" --iam-instance-profile Name="$PERFIL_EC2" --user-data "$USERDATA" \
    "${extra[@]}" --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=20}' \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$nombre}]" \
    --query 'Instances[0].InstanceId' --output text
}

echo "== Lanzando instancias =="
DB=$(lanzar PP-DB-Tier "$SUB_A" "$SG_DB" no)
APP1=$(lanzar PP-App-Tier "$SUB_A" "$SG_APP" si)
APP2=$(lanzar PP-App-Tier-2 "$SUB_B" "$SG_APP" si)
INGEST=$(lanzar PP-Ingest-VM "$SUB_A" "$SG_INGEST" no)
guardar DB "$DB"
guardar APP1 "$APP1"
guardar APP2 "$APP2"
guardar INGEST "$INGEST"

echo "Esperando a que arranquen..."
aws ec2 wait instance-running --instance-ids "$DB" "$APP1" "$APP2" "$INGEST"

DB_IP=$(aws ec2 describe-instances --instance-ids "$DB" --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)
guardar DB_IP "$DB_IP"

echo "DB=$DB APP1=$APP1 APP2=$APP2 INGEST=$INGEST"
echo "IP privada de la BD: $DB_IP"

esperar_ssm "$DB"
esperar_ssm "$APP1"
esperar_ssm "$APP2"
esperar_ssm "$INGEST"
echo "Las 4 instancias responden por SSM."
