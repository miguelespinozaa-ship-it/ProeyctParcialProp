import os
import time
from typing import Optional

import boto3

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
ATHENA_DATABASE = os.getenv("ATHENA_DATABASE", "ubereats_datalake")
ATHENA_OUTPUT_S3 = os.getenv("ATHENA_OUTPUT_S3", "s3://ubereats-datalake-utec/athena-results/")

# Con ATHENA_MOCK=true (default) los endpoints devuelven datos de ejemplo con la misma forma
# que las vistas reales. Poner ATHENA_MOCK=false con credenciales AWS válidas para consultar Athena.
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

    # get_query_results pagina de a 1000 filas: sigue NextToken hasta agotarlo.
    columns: Optional[list[str]] = None
    rows: list[dict] = []
    next_token = None
    first_page = True
    while True:
        kwargs = {"QueryExecutionId": exec_id, "MaxResults": 1000}
        if next_token:
            kwargs["NextToken"] = next_token
        result = client.get_query_results(**kwargs)

        result_rows = result["ResultSet"]["Rows"]
        if first_page:
            columns = [c["Label"] for c in result["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]]
            result_rows = result_rows[1:]  # la primera fila de la primera página son los encabezados
            first_page = False

        for row in result_rows:
            values = [f.get("VarCharValue") for f in row["Data"]]
            rows.append(dict(zip(columns, values)))

        next_token = result.get("NextToken")
        if not next_token:
            break

    return rows
