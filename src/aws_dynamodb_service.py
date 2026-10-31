import os
import time
import boto3
from datetime import datetime

REGION = os.getenv("AWS_REGION", "ap-south-1")
TABLE_NAME = os.getenv("DYNAMODB_TABLE", "StockSentiment-LiveFeed")

_dynamodb_client = None

def get_dynamodb_client():
    global _dynamodb_client
    if _dynamodb_client is None:
        try:
            _dynamodb_client = boto3.client('dynamodb', region_name=REGION)
        except Exception as e:
            print(f"Warning: Could not initialize DynamoDB client: {e}")
    return _dynamodb_client

def publish_sentiment_event(ticker: str, source: str, title: str, sentiment: float, label: str, url: str = "", metadata: dict = None):
    """
    Publish a single analyzed sentiment event to DynamoDB StockSentiment-LiveFeed.
    Triggers DynamoDB Streams -> AWS Lambda in real time.
    """
    client = get_dynamodb_client()
    if not client:
        return False

    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    event_id = f"{ticker.upper()}-{int(time.time()*1000)}"

    item = {
        "ticker": {"S": ticker.upper()},
        "timestamp": {"S": now_iso},
        "eventId": {"S": event_id},
        "source": {"S": source.lower()},
        "title": {"S": str(title)[:300]},
        "sentiment": {"N": f"{float(sentiment):.4f}"},
        "label": {"S": str(label)},
        "url": {"S": str(url)[:500] if url else ""}
    }

    if metadata:
        for k, v in metadata.items():
            if v is not None:
                item[f"meta_{k}"] = {"S": str(v)[:200]}

    try:
        client.put_item(TableName=TABLE_NAME, Item=item)
        return True
    except Exception as e:
        print(f"Notice: Failed to buffer item in DynamoDB: {e}")
        return False

def batch_publish_sentiment_events(events: list):
    """
    Batch publish up to 25 items at a time to DynamoDB.
    """
    client = get_dynamodb_client()
    if not client or not events:
        return 0

    success_count = 0
    # Process in batches of 25 (DynamoDB batch_write_item limit)
    for i in range(0, len(events), 25):
        chunk = events[i:i+25]
        request_items = []
        for idx, ev in enumerate(chunk):
            unique_ts = f"{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')}_{idx:02d}"
            ticker = str(ev.get("ticker", "MARKET")).upper()
            item = {
                "ticker": {"S": ticker},
                "timestamp": {"S": str(ev.get("timestamp", unique_ts))},
                "source": {"S": str(ev.get("source", "feed")).lower()},
                "title": {"S": str(ev.get("title", ""))[:300]},
                "sentiment": {"N": f"{float(ev.get('sentiment', 0.0)):.4f}"},
                "label": {"S": str(ev.get("label", "Neutral"))},
                "url": {"S": str(ev.get("url", ""))[:500]}
            }
            request_items.append({"PutRequest": {"Item": item}})

        try:
            client.batch_write_item(RequestItems={TABLE_NAME: request_items})
            success_count += len(request_items)
        except Exception as e:
            print(f"Notice during batch write to DynamoDB: {e}")

    return success_count
