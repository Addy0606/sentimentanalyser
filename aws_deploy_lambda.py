import boto3
import zipfile
import time
import os

REGION = "ap-south-1"
ACCOUNT_ID = "136127964165"
FUNCTION_NAME = "StockSentiment-StreamProcessor"
ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/StockSentiment-LambdaRole"
TABLE_NAME = "StockSentiment-LiveFeed"

session = boto3.Session(region_name=REGION)
lambda_client = session.client('lambda')
dynamodb = session.client('dynamodb')

# 1. Package zip artifact
zip_path = "aws/lambda_stream_processor.zip"
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
    z.write("aws/lambda_stream_processor.py", "lambda_function.py")
print("1. Packaged Lambda deployment artifact:", zip_path)

with open(zip_path, 'rb') as f:
    zip_bytes = f.read()

# 2. Get or create Lambda function
print("2. Checking Lambda function:", FUNCTION_NAME)
try:
    lambda_client.get_function(FunctionName=FUNCTION_NAME)
    print("Function exists. Updating code...")
    res = lambda_client.update_function_code(
        FunctionName=FUNCTION_NAME,
        ZipFile=zip_bytes
    )
    print("Updated function code.")
except Exception:
    print("Function does not exist. Creating new Lambda function...")
    time.sleep(5)  # Wait briefly for IAM role propagation
    res = lambda_client.create_function(
        FunctionName=FUNCTION_NAME,
        Runtime='python3.12',
        Role=ROLE_ARN,
        Handler='lambda_function.lambda_handler',
        Code={'ZipFile': zip_bytes},
        Description='Consumes StockSentiment-LiveFeed stream, computes divergence and publishes CloudWatch metrics',
        Timeout=15,
        MemorySize=128
    )
    print("Created Lambda function:", res['FunctionArn'])

# 3. Get DynamoDB Stream ARN
desc = dynamodb.describe_table(TableName=TABLE_NAME)
stream_arn = desc['Table'].get('LatestStreamArn')
print(f"DynamoDB Stream ARN: {stream_arn}")

if stream_arn:
    # 4. Check or create Event Source Mapping
    mappings = lambda_client.list_event_source_mappings(
        FunctionName=FUNCTION_NAME,
        EventSourceArn=stream_arn
    )['EventSourceMappings']

    if mappings:
        print(f"Event Source Mapping already active (UUID: {mappings[0]['UUID']}).")
    else:
        print("Creating Event Source Mapping for DynamoDB Streams...")
        esm_resp = lambda_client.create_event_source_mapping(
            EventSourceArn=stream_arn,
            FunctionName=FUNCTION_NAME,
            Enabled=True,
            BatchSize=10,
            StartingPosition='LATEST'
        )
        print("Created Event Source Mapping (UUID:", esm_resp['UUID'], ")")

print("\n=== Lambda Stream Processor Deployed and Wired Successfully! ===")
