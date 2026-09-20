"""Ingesta Pull 100% - MySQL (usuarios, direcciones) -> CSV -> S3.

Corre una vez por invocación (no es un servicio persistente). Pensado para correr en la
MV de Ingesta, contra el MySQL de la MV de BD (EC2 #2) y subir a un bucket S3 del data lake.
"""
import io
import os
from datetime import datetime, timezone

import boto3
import pandas as pd
from sqlalchemy import create_engine

DB_HOST = os.environ["MYSQL_HOST"]
DB_PORT = os.getenv("MYSQL_PORT", "3306")
DB_USER = os.environ["MYSQL_USER"]
DB_PASSWORD = os.environ["MYSQL_PASSWORD"]
DB_NAME = os.getenv("MYSQL_DATABASE", "ms1_usuarios")

S3_BUCKET = os.environ["S3_BUCKET"]
S3_PREFIX = os.getenv("S3_PREFIX", "raw/mysql")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

TABLES = ["usuarios", "direcciones"]


def replace_prefix(s3, prefix):
    """Full refresh: borra el snapshot anterior de esta tabla antes de subir el nuevo.
    Sin esto, dos corridas (dt=fecha distinta) quedan como dos particiones y Athena las suma."""
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix):
        objs = [{"Key": o["Key"]} for o in page.get("Contents", [])]
        if objs:
            s3.delete_objects(Bucket=S3_BUCKET, Delete={"Objects": objs})


def main():
    engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    s3 = boto3.client("s3", region_name=AWS_REGION)
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for table in TABLES:
        print(f"Extrayendo tabla {table}...")
        df = pd.read_sql_table(table, engine)
        print(f"  {len(df)} filas")

        buffer = io.StringIO()
        df.to_csv(buffer, index=False)

        # dt=YYYY-MM-DD como partición Hive-style: Glue Crawler la detecta automáticamente.
        key = f"{S3_PREFIX}/{table}/dt={run_date}/{table}.csv"
        replace_prefix(s3, f"{S3_PREFIX}/{table}/")
        s3.put_object(Bucket=S3_BUCKET, Key=key, Body=buffer.getvalue().encode("utf-8"))
        print(f"  subido a s3://{S3_BUCKET}/{key}")

    print("Ingesta MySQL completa.")


if __name__ == "__main__":
    main()
