import os
import time
from typing import Optional

import boto3

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
ATHENA_DATABASE = os.getenv("ATHENA_DATABASE", "ubereats_datalake")
ATHENA_OUTPUT_S3 = os.getenv("ATHENA_OUTPUT_S3", "s3://ubereats-datalake-utec/athena-results/")

# Fase 8: sin el pipeline de Fase 9 (Glue/Athena poblado) no hay nada real contra qué consultar.
# Con ATHENA_MOCK=true (default) los endpoints devuelven datos de ejemplo con la misma forma
# que las vistas documentadas. Poner ATHENA_MOCK=false (con credenciales reales) en Fase 9/10.
ATHENA_MOCK = os.getenv("ATHENA_MOCK", "true").lower() == "true"

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client("athena", region_name=AWS_REGION)
    return _client


def run_query(query: str, poll_interval: float = 1.0, timeout: float = 30.0) -> list[dict]:
    """Ejecuta una query contra Athena y devuelve las filas como lista de dicts.

    Solo se llama cuando ATHENA_MOCK=false. Usa start_query_execution / get_query_execution /
    get_query_results del cliente boto3, contra ATHENA_DATABASE y ATHENA_OUTPUT_S3.
    """
    client = _get_client()
    exec_id = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": ATHENA_DATABASE},
        ResultConfiguration={"OutputLocation": ATHENA_OUTPUT_S3},
    )["QueryExecutionId"]

    status: Optional[str] = None
    elapsed = 0.0
    while elapsed < timeout:
        status = client.get_query_execution(QueryExecutionId=exec_id)["QueryExecution"]["Status"]["State"]
        if status in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(poll_interval)
        elapsed += poll_interval

    if status != "SUCCEEDED":
        raise RuntimeError(f"Athena query terminó en estado {status}")

    result = client.get_query_results(QueryExecutionId=exec_id)
    columns = [c["Label"] for c in result["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]]
    rows = []
    for row in result["ResultSet"]["Rows"][1:]:  # la primera fila son los encabezados
        values = [f.get("VarCharValue") for f in row["Data"]]
        rows.append(dict(zip(columns, values)))
    return rows
