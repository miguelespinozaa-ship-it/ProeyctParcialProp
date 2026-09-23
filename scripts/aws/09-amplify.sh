#!/usr/bin/env bash
# Frontend en AWS Amplify. Con GITHUB_TOKEN (token personal de GitHub, permiso repo)
# conecta el repositorio y queda con CI/CD. Sin token, crea la app y deja los pasos
# manuales para conectar GitHub desde la consola (requiere autorizar OAuth en el navegador).
source "$(dirname "$0")/lib.sh"

APP_ID=$(aws amplify list-apps --query "apps[?name=='pp-frontend'].appId" --output text)

if [ -n "${GITHUB_TOKEN:-}" ]; then
  if [ -z "$APP_ID" ]; then
    APP_ID=$(aws amplify create-app --name pp-frontend --platform WEB \
      --repository "$REPO_URL_HTTPS" --access-token "$GITHUB_TOKEN" \
      --environment-variables VITE_API_BASE_URL="$GATEWAY_URL" \
      --query 'app.appId' --output text)
    aws amplify create-branch --app-id "$APP_ID" --branch-name main --enable-auto-build >/dev/null
    aws amplify update-app --app-id "$APP_ID" --custom-rules '[{"source":"</^[^.]+$|\\.(?!(css|gif|ico|jpg|js|png|txt|svg|woff|woff2|ttf|map|json|webp)$)([^.]+$)/>","target":"/index.html","status":"200"}]' >/dev/null
    JOB=$(aws amplify start-job --app-id "$APP_ID" --branch-name main --job-type RELEASE --query 'jobSummary.jobId' --output text)
    echo "Compilando (job $JOB)..."
    for _ in $(seq 1 40); do
      estado=$(aws amplify get-job --app-id "$APP_ID" --branch-name main --job-id "$JOB" --query 'job.summary.status' --output text)
      [ "$estado" = "SUCCEED" ] || [ "$estado" = "FAILED" ] && break
      sleep 15
    done
    echo "Estado del build: $estado"
  else
    echo "La app de Amplify ya existe (appId=$APP_ID)."
  fi
  guardar AMPLIFY_APP_ID "$APP_ID"
  DOMAIN=$(aws amplify get-app --app-id "$APP_ID" --query 'app.defaultDomain' --output text)
  echo "Frontend: https://main.$DOMAIN"
else
  if [ -z "$APP_ID" ]; then
    APP_ID=$(aws amplify create-app --name pp-frontend --platform WEB \
      --environment-variables VITE_API_BASE_URL="$GATEWAY_URL" --query 'app.appId' --output text)
    aws amplify update-app --app-id "$APP_ID" --custom-rules '[{"source":"</^[^.]+$|\\.(?!(css|gif|ico|jpg|js|png|txt|svg|woff|woff2|ttf|map|json|webp)$)([^.]+$)/>","target":"/index.html","status":"200"}]' >/dev/null
  fi
  guardar AMPLIFY_APP_ID "$APP_ID"
  cat <<MSG

App de Amplify creada (appId=$APP_ID), sin conectar a GitHub todavia.
Para conectarla (requiere autorizar en el navegador, no se puede automatizar sin un
token personal de GitHub):

  1. Consola -> AWS Amplify -> pp-frontend -> Connect branch -> GitHub -> autorizar.
  2. Elegir el repositorio y la rama main, carpeta raiz "frontend" (monorepo).
  3. Guardar y desplegar.

O, para automatizarlo del todo: generar un token personal de GitHub (permiso "repo")
y volver a correr este script con GITHUB_TOKEN=<token> ./09-amplify.sh
MSG
fi
