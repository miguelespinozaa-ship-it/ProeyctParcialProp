#!/usr/bin/env bash
# Variables y funciones comunes. Los demas scripts hacen: source "$(dirname "$0")/lib.sh"
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_FILE="$DIR/state.env"
REPO_URL_HTTPS="https://github.com/miguelespinozaa-ship-it/ProeyctParcialProp.git"
REGION="${AWS_REGION:-us-east-1}"
export AWS_DEFAULT_REGION="$REGION"

touch "$STATE_FILE"
# shellcheck disable=SC1090
source "$STATE_FILE"

# Guarda una variable en state.env para que los siguientes scripts la lean.
guardar() {
  local clave="$1" valor="$2"
  sed -i "/^${clave}=/d" "$STATE_FILE" 2>/dev/null || true
  echo "${clave}=\"${valor}\"" >> "$STATE_FILE"
  export "${clave}=${valor}"
}

# Espera a que una instancia responda por SSM (agente registrado).
esperar_ssm() {
  local id="$1"
  echo "Esperando agente SSM en $id..."
  for _ in $(seq 1 30); do
    estado=$(aws ssm describe-instance-information \
      --filters "Key=InstanceIds,Values=$id" \
      --query 'InstanceInformationList[0].PingStatus' --output text 2>/dev/null || echo "None")
    [ "$estado" = "Online" ] && return 0
    sleep 10
  done
  echo "SSM no respondio a tiempo en $id" >&2
  exit 1
}

# Corre un script remoto por SSM (sin SSH) y espera el resultado.
# Uso: ssm_run <instance-id> <<'EOF' ...script... EOF
ssm_run() {
  local id="$1"
  local script; script="$(cat)"
  local params; params="$(python3 -c '
import json, sys
print(json.dumps({"commands": [sys.stdin.read()]}))
' <<< "$script")"
  echo "$params" > /tmp/ssm-params-$$.json
  local cid
  cid=$(aws ssm send-command --document-name AWS-RunShellScript --instance-ids "$id" \
    --parameters file:///tmp/ssm-params-$$.json --query Command.CommandId --output text)
  rm -f /tmp/ssm-params-$$.json
  aws ssm wait command-executed --command-id "$cid" --instance-id "$id" 2>/dev/null || true
  local status
  status=$(aws ssm get-command-invocation --command-id "$cid" --instance-id "$id" --query Status --output text)
  aws ssm get-command-invocation --command-id "$cid" --instance-id "$id" --query StandardOutputContent --output text
  if [ "$status" != "Success" ]; then
    echo "--- error en $id (status=$status) ---" >&2
    aws ssm get-command-invocation --command-id "$cid" --instance-id "$id" --query StandardErrorContent --output text >&2
    exit 1
  fi
}

# AMI de Ubuntu 22.04 mas reciente (Canonical) en la region actual.
ami_ubuntu_22_04() {
  aws ec2 describe-images --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" "Name=state,Values=available" \
    --query 'sort_by(Images,&CreationDate)[-1].ImageId' --output text
}
