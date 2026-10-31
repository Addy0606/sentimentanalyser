import os
import json
import boto3
import pandas as pd
from datetime import datetime

REGION = os.getenv("AWS_REGION", "ap-south-1")
ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "136127964165")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME", f"stock-sentiment-archive-{ACCOUNT_ID}")

_s3_client = None

def get_s3_client():
    global _s3_client
    if _s3_client is None:
        try:
            _s3_client = boto3.client('s3', region_name=REGION)
        except Exception as e:
            print(f"Warning: Could not initialize S3 client: {e}")
    return _s3_client

def archive_raw_payload(source: str, payload: list) -> str:
    """
    Archives raw JSON scraped data into S3 partitioned by date.
    e.g. s3://bucket/raw/reddit/year=2026/month=10/day=13/reddit_1697200000.json
    """
    client = get_s3_client()
    if not client or not payload:
        return ""

    now = datetime.utcnow()
    key = (
        f"raw/{source.lower()}/year={now.year}/month={now.month:02d}/day={now.day:02d}/"
        f"{source.lower()}_{int(now.timestamp())}.json"
    )

    try:
        client.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=json.dumps(payload, default=str),
            ContentType="application/json"
        )
        return key
    except Exception as e:
        print(f"Notice: Failed to archive to S3: {e}")
        return ""

def upload_daily_digest(summary_df: pd.DataFrame) -> dict:
    """
    Generates a daily market sentiment digest CSV and uploads to S3.
    Returns the S3 Key and a 60-minute Pre-Signed Download URL.
    """
    client = get_s3_client()
    if not client or summary_df.empty:
        return {"key": "", "url": ""}

    now = datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")
    key = f"reports/{date_str}/daily_market_sentiment_digest_{date_str}.csv"

    csv_data = summary_df.to_csv(index=False)

    try:
        client.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=csv_data.encode("utf-8"),
            ContentType="text/csv"
        )

        presigned_url = client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': key},
            ExpiresIn=3600
        )

        return {"key": key, "url": presigned_url}
    except Exception as e:
        print(f"Notice: Failed to upload digest to S3: {e}")
        return {"key": "", "url": ""}

def get_latest_digest_presigned_url(date_str: str = None) -> str:
    """
    Returns a Pre-Signed URL for the day's digest.
    """
    client = get_s3_client()
    if not client:
        return ""

    if not date_str:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    key = f"reports/{date_str}/daily_market_sentiment_digest_{date_str}.csv"

    try:
        return client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': key},
            ExpiresIn=3600
        )
    except Exception as e:
        print(f"Notice: Could not generate presigned URL: {e}")
        return ""
