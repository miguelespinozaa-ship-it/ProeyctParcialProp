"""Ingesta Pull 100% - PostgreSQL (orders, order_items) -> CSV -> S3.

Corre una vez por invocación. Mismo patrón que ingest-mysql.
"""
import io
import os
from datetime import datetime, timezone

import boto3
import pandas as pd
from sqlalchemy import create_engine

DB_HOST = os.environ["PG_HOST"]
DB_PORT = os.getenv("PG_PORT", "5432")
DB_USER = os.environ["PG_USER"]
DB_PASSWORD = os.environ["PG_PASSWORD"]
DB_NAME = os.getenv("PG_DATABASE", "ms3_pedidos")

S3_BUCKET = os.environ["S3_BUCKET"]
S3_PREFIX = os.getenv("S3_PREFIX", "raw/postgres")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

TABLES = ["orders", "order_items"]


def replace_prefix(s3, prefix):
    """Full refresh: borra el snapshot anterior de esta tabla antes de subir el nuevo.
    Sin esto, dos corridas (dt=fecha distinta) quedan como dos particiones y Athena las suma."""
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix):
        objs = [{"Key": o["Key"]} for o in page.get("Contents", [])]
        if objs:
            s3.delete_objects(Bucket=S3_BUCKET, Delete={"Objects": objs})


def main():
    engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    s3 = boto3.client("s3", region_name=AWS_REGION)
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for table in TABLES:
        print(f"Extrayendo tabla {table}...")
        df = pd.read_sql_table(table, engine)
        print(f"  {len(df)} filas")

        buffer = io.StringIO()
        df.to_csv(buffer, index=False)

        key = f"{S3_PREFIX}/{table}/dt={run_date}/{table}.csv"
        replace_prefix(s3, f"{S3_PREFIX}/{table}/")
        s3.put_object(Bucket=S3_BUCKET, Key=key, Body=buffer.getvalue().encode("utf-8"))
        print(f"  subido a s3://{S3_BUCKET}/{key}")

    print("Ingesta PostgreSQL completa.")


if __name__ == "__main__":
    main()
