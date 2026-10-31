import boto3
import json
import time

REGION = "ap-south-1"
ACCOUNT_ID = "136127964165"
BUCKET_NAME = f"stock-sentiment-archive-{ACCOUNT_ID}"
TABLE_NAME = "StockSentiment-LiveFeed"

session = boto3.Session(region_name=REGION)
s3 = session.client('s3')
dynamodb = session.client('dynamodb')

print("1. Setting up S3 Bucket:", BUCKET_NAME)
try:
    s3.head_bucket(Bucket=BUCKET_NAME)
    print(f"Bucket '{BUCKET_NAME}' already exists.")
except Exception:
    print(f"Creating bucket '{BUCKET_NAME}'...")
    s3.create_bucket(
        Bucket=BUCKET_NAME,
        CreateBucketConfiguration={'LocationConstraint': REGION}
    )
    print(f"Bucket '{BUCKET_NAME}' created successfully.")

# Setup CORS for Streamlit / Web UI access
try:
    s3.put_bucket_cors(
        Bucket=BUCKET_NAME,
        CORSConfiguration={
            'CORSRules': [{
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'PUT', 'HEAD'],
                'AllowedOrigins': ['*'],
                'MaxAgeSeconds': 3000
            }]
        }
    )
    print("S3 CORS configured successfully.")
except Exception as e:
    print("CORS configuration notice:", e)

print("\n2. Setting up DynamoDB Table:", TABLE_NAME)
try:
    desc = dynamodb.describe_table(TableName=TABLE_NAME)
    print(f"Table '{TABLE_NAME}' already exists. Status: {desc['Table']['TableStatus']}")
    stream_arn = desc['Table'].get('LatestStreamArn')
except Exception:
    print(f"Creating table '{TABLE_NAME}' with Streams enabled...")
    table_resp = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {'AttributeName': 'ticker', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'ticker', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST',
        StreamSpecification={
            'StreamEnabled': True,
            'StreamViewType': 'NEW_AND_OLD_IMAGES'
        }
    )
    print(f"Table creation requested. Waiting for ACTIVE status...")
    waiter = dynamodb.get_waiter('table_exists')
    waiter.wait(TableName=TABLE_NAME)
    desc = dynamodb.describe_table(TableName=TABLE_NAME)
    stream_arn = desc['Table'].get('LatestStreamArn')
    print(f"Table '{TABLE_NAME}' is now ACTIVE.")

print(f"DynamoDB Stream ARN: {stream_arn}")

# 3. Setup Extra DynamoDB Tables: API Quota Tracker & Influencer Reputation
EXTRA_TABLES = [
    {
        "TableName": "StockSentiment-APIQuotaTracker",
        "KeySchema": [
            {'AttributeName': 'apiProvider', 'KeyType': 'HASH'},
            {'AttributeName': 'requestDate', 'KeyType': 'RANGE'}
        ],
        "AttributeDefinitions": [
            {'AttributeName': 'apiProvider', 'AttributeType': 'S'},
            {'AttributeName': 'requestDate', 'AttributeType': 'S'}
        ]
    },
    {
        "TableName": "StockSentiment-InfluencerReputation",
        "KeySchema": [
            {'AttributeName': 'author', 'KeyType': 'HASH'},
            {'AttributeName': 'subreddit', 'KeyType': 'RANGE'}
        ],
        "AttributeDefinitions": [
            {'AttributeName': 'author', 'AttributeType': 'S'},
            {'AttributeName': 'subreddit', 'AttributeType': 'S'}
        ]
    }
]

print("\n3. Setting up Extra DynamoDB Tables (APIQuotaTracker, InfluencerReputation)...")
for tbl in EXTRA_TABLES:
    name = tbl["TableName"]
    try:
        d = dynamodb.describe_table(TableName=name)
        print(f"Table '{name}' already exists. Status: {d['Table']['TableStatus']}")
    except Exception:
        print(f"Creating table '{name}'...")
        dynamodb.create_table(
            TableName=name,
            KeySchema=tbl["KeySchema"],
            AttributeDefinitions=tbl["AttributeDefinitions"],
            BillingMode='PAY_PER_REQUEST'
        )
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=name)
        print(f"Table '{name}' is now ACTIVE.")

print("\n=== Resource Provisioning Completed Successfully! ===")
