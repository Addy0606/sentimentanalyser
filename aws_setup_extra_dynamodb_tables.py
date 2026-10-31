import boto3
import time

REGION = "ap-south-1"
ACCOUNT_ID = "136127964165"

session = boto3.Session(region_name=REGION)
dynamodb = session.client('dynamodb')

TABLES = [
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

print("=== Setting up Extra DynamoDB Tables in ap-south-1 ===")

for tbl in TABLES:
    name = tbl["TableName"]
    try:
        desc = dynamodb.describe_table(TableName=name)
        print(f"Table '{name}' already exists. Status: {desc['Table']['TableStatus']}")
    except Exception:
        print(f"Creating table '{name}' with PAY_PER_REQUEST billing...")
        dynamodb.create_table(
            TableName=name,
            KeySchema=tbl["KeySchema"],
            AttributeDefinitions=tbl["AttributeDefinitions"],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"Waiting for '{name}' to become ACTIVE...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=name)
        print(f"Table '{name}' is now ACTIVE.")

print("\n=== Seeding Tables with Initial Records ===")

# 1. Seed API Quota Tracker
api_items = [
    {
        "apiProvider": {"S": "NewsAPI"},
        "requestDate": {"S": "2026-10-31"},
        "callsUsedToday": {"N": "24"},
        "dailyLimit": {"N": "100"},
        "remainingQuota": {"N": "76"},
        "lastCallTimestamp": {"S": "2026-10-31T17:45:00Z"},
        "tier": {"S": "Developer-FreeTier"},
        "status": {"S": "HEALTHY"}
    },
    {
        "apiProvider": {"S": "Reddit_PRAW"},
        "requestDate": {"S": "2026-10-31"},
        "callsUsedToday": {"N": "180"},
        "dailyLimit": {"N": "10000"},
        "remainingQuota": {"N": "9820"},
        "lastCallTimestamp": {"S": "2026-10-31T17:46:12Z"},
        "tier": {"S": "Script-OAuth2"},
        "status": {"S": "HEALTHY"}
    },
    {
        "apiProvider": {"S": "Google_Gemini"},
        "requestDate": {"S": "2026-10-31"},
        "callsUsedToday": {"N": "18"},
        "dailyLimit": {"N": "1500"},
        "remainingQuota": {"N": "1482"},
        "lastCallTimestamp": {"S": "2026-10-31T17:47:00Z"},
        "tier": {"S": "Interactions-API"},
        "status": {"S": "HEALTHY"}
    }
]

for item in api_items:
    dynamodb.put_item(TableName="StockSentiment-APIQuotaTracker", Item=item)
    print(f"  [OK] Seeded API quota for: {item['apiProvider']['S']}")

# 2. Seed Influencer Reputation
influencer_items = [
    {
        "author": {"S": "DeepValueHunter"},
        "subreddit": {"S": "stocks"},
        "karmaScore": {"N": "48200"},
        "weightMultiplier": {"N": "1.85"},
        "accuracyRating": {"S": "88%"},
        "primaryTickerFocus": {"S": "RELIANCE"},
        "sentimentBias": {"S": "Neutral-Bullish"},
        "verified": {"BOOL": True},
        "lastActive": {"S": "2026-10-31T16:30:00Z"}
    },
    {
        "author": {"S": "DalalStreetBull"},
        "subreddit": {"S": "IndianStockMarket"},
        "karmaScore": {"N": "31500"},
        "weightMultiplier": {"N": "1.60"},
        "accuracyRating": {"S": "82%"},
        "primaryTickerFocus": {"S": "TCS"},
        "sentimentBias": {"S": "Bullish"},
        "verified": {"BOOL": True},
        "lastActive": {"S": "2026-10-31T17:15:00Z"}
    },
    {
        "author": {"S": "QuantTrader99"},
        "subreddit": {"S": "investing"},
        "karmaScore": {"N": "65400"},
        "weightMultiplier": {"N": "2.00"},
        "accuracyRating": {"S": "91%"},
        "primaryTickerFocus": {"S": "INFY"},
        "sentimentBias": {"S": "Analytical"},
        "verified": {"BOOL": True},
        "lastActive": {"S": "2026-10-31T15:20:00Z"}
    },
    {
        "author": {"S": "TechAnalystPro"},
        "subreddit": {"S": "stocks"},
        "karmaScore": {"N": "28900"},
        "weightMultiplier": {"N": "1.45"},
        "accuracyRating": {"S": "79%"},
        "primaryTickerFocus": {"S": "NVDA"},
        "sentimentBias": {"S": "Bullish"},
        "verified": {"BOOL": False},
        "lastActive": {"S": "2026-10-31T14:40:00Z"}
    },
    {
        "author": {"S": "RetailApeTrader"},
        "subreddit": {"S": "wallstreetbets"},
        "karmaScore": {"N": "12400"},
        "weightMultiplier": {"N": "0.90"},
        "accuracyRating": {"S": "61%"},
        "primaryTickerFocus": {"S": "HDFCBANK"},
        "sentimentBias": {"S": "High-Volatility"},
        "verified": {"BOOL": False},
        "lastActive": {"S": "2026-10-31T17:05:00Z"}
    }
]

for item in influencer_items:
    dynamodb.put_item(TableName="StockSentiment-InfluencerReputation", Item=item)
    print(f"  [OK] Seeded influencer profile for: {item['author']['S']} (r/{item['subreddit']['S']})")

print("\n=== All Extra DynamoDB Tables Created & Seeded Successfully! ===")

