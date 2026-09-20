"""Ingesta Pull 100% - MongoDB (restaurantes) -> JSONL -> S3.

Corre una vez por invocación. JSONL (un documento JSON por línea) para que el Glue Crawler
infiera el esquema anidado (platos[], resenas[]) sin aplanarlo a mano.
"""
import json
import os
from datetime import datetime, timezone

import boto3
from bson import json_util
from pymongo import MongoClient

MONGO_URI = os.environ["MONGO_URI"]
DB_NAME = os.getenv("MONGO_DB", "ms2_catalogo")
COLLECTION = os.getenv("MONGO_COLLECTION", "restaurantes")

S3_BUCKET = os.environ["S3_BUCKET"]
S3_PREFIX = os.getenv("S3_PREFIX", "raw/mongodb")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


def replace_prefix(s3, prefix):
    """Full refresh: borra el snapshot anterior de esta tabla antes de subir el nuevo.
    Sin esto, dos corridas (dt=fecha distinta) quedan como dos particiones y Athena las suma."""
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix):
        objs = [{"Key": o["Key"]} for o in page.get("Contents", [])]
        if objs:
            s3.delete_objects(Bucket=S3_BUCKET, Delete={"Objects": objs})


def main():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    s3 = boto3.client("s3", region_name=AWS_REGION)
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print(f"Extrayendo colección {COLLECTION}...")
    # json_util.default serializa ObjectId/fechas de Mongo a algo que Athena pueda leer como string.
    lines = [json.dumps(doc, default=json_util.default) for doc in db[COLLECTION].find()]
    print(f"  {len(lines)} documentos")

    body = "\n".join(lines).encode("utf-8")
    key = f"{S3_PREFIX}/{COLLECTION}/dt={run_date}/{COLLECTION}.jsonl"
    replace_prefix(s3, f"{S3_PREFIX}/{COLLECTION}/")
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=body)
    print(f"  subido a s3://{S3_BUCKET}/{key}")
    print("Ingesta MongoDB completa.")


if __name__ == "__main__":
    main()
