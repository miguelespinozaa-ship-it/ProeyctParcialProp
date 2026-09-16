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
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=body)
    print(f"  subido a s3://{S3_BUCKET}/{key}")
    print("Ingesta MongoDB completa.")


if __name__ == "__main__":
    main()
