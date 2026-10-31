import boto3
import json

REGION = "ap-south-1"
ACCOUNT_ID = "136127964165"

ec2 = boto3.client('ec2', region_name=REGION)
iam = boto3.client('iam', region_name=REGION)

# 1. Setup Security Groups
print("1. Setting up Security Groups...")
vpcs = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])['Vpcs']
if not vpcs:
    vpcs = ec2.describe_vpcs()['Vpcs']
vpc_id = vpcs[0]['VpcId']
print(f"Using VPC: {vpc_id}")

ec2_sg_id = None
try:
    sgs = ec2.describe_security_groups(
        Filters=[{'Name': 'group-name', 'Values': ['StockSentiment-EC2-SG']}]
    )['SecurityGroups']
    if sgs:
        ec2_sg_id = sgs[0]['GroupId']
        print(f"Security Group 'StockSentiment-EC2-SG' already exists ({ec2_sg_id}).")
    else:
        resp = ec2.create_security_group(
            GroupName='StockSentiment-EC2-SG',
            Description='Security Group for Stock Sentiment EC2 instance',
            VpcId=vpc_id
        )
        ec2_sg_id = resp['GroupId']
        print(f"Created Security Group 'StockSentiment-EC2-SG': {ec2_sg_id}")
        
        # Authorize ports 8501 (Streamlit), 80 (HTTP), 22 (SSH)
        ec2.authorize_security_group_ingress(
            GroupId=ec2_sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 8501,
                    'ToPort': 8501,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'Streamlit Dashboard'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTP Web'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'SSH Management'}]
                }
            ]
        )
        print("Configured inbound rules for StockSentiment-EC2-SG.")
except Exception as e:
    print(f"Notice during EC2 SG setup: {e}")

# RDS Security Group
try:
    sgs = ec2.describe_security_groups(
        Filters=[{'Name': 'group-name', 'Values': ['StockSentiment-RDS-SG']}]
    )['SecurityGroups']
    if sgs:
        rds_sg_id = sgs[0]['GroupId']
        print(f"Security Group 'StockSentiment-RDS-SG' already exists ({rds_sg_id}).")
    else:
        resp = ec2.create_security_group(
            GroupName='StockSentiment-RDS-SG',
            Description='Security Group for Stock Sentiment RDS Database',
            VpcId=vpc_id
        )
        rds_sg_id = resp['GroupId']
        print(f"Created Security Group 'StockSentiment-RDS-SG': {rds_sg_id}")
        
        # Inbound from EC2 SG
        if ec2_sg_id:
            ec2.authorize_security_group_ingress(
                GroupId=rds_sg_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 5432,
                        'ToPort': 5432,
                        'UserIdGroupPairs': [{'GroupId': ec2_sg_id, 'Description': 'PostgreSQL from EC2 SG'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 1433,
                        'ToPort': 1433,
                        'UserIdGroupPairs': [{'GroupId': ec2_sg_id, 'Description': 'SQL Server from EC2 SG'}]
                    }
                ]
            )
            print("Configured inbound rules for StockSentiment-RDS-SG.")
except Exception as e:
    print(f"Notice during RDS SG setup: {e}")

# 2. Setup IAM Roles
print("\n2. Setting up IAM Roles...")

# EC2 Role
ec2_trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "ec2.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}

try:
    iam.get_role(RoleName='StockSentiment-EC2Role')
    print("Role 'StockSentiment-EC2Role' already exists.")
except Exception:
    iam.create_role(
        RoleName='StockSentiment-EC2Role',
        AssumeRolePolicyDocument=json.dumps(ec2_trust_policy),
        Description='IAM Role for Stock Sentiment EC2 instance'
    )
    print("Created IAM Role 'StockSentiment-EC2Role'.")

# Attach inline policy to EC2 Role for S3, DynamoDB, CloudWatch
ec2_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                f"arn:aws:s3:::stock-sentiment-archive-{ACCOUNT_ID}",
                f"arn:aws:s3:::stock-sentiment-archive-{ACCOUNT_ID}/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": f"arn:aws:dynamodb:{REGION}:{ACCOUNT_ID}:table/StockSentiment-*"
        },
        {
            "Effect": "Allow",
            "Action": ["cloudwatch:PutMetricData"],
            "Resource": "*"
        }
    ]
}
iam.put_role_policy(
    RoleName='StockSentiment-EC2Role',
    PolicyName='StockSentiment-EC2AccessPolicy',
    PolicyDocument=json.dumps(ec2_policy)
)
print("Attached policy to 'StockSentiment-EC2Role'.")

# Instance Profile
try:
    iam.get_instance_profile(InstanceProfileName='StockSentiment-EC2InstanceProfile')
    print("Instance profile 'StockSentiment-EC2InstanceProfile' already exists.")
except Exception:
    iam.create_instance_profile(InstanceProfileName='StockSentiment-EC2InstanceProfile')
    iam.add_role_to_instance_profile(
        InstanceProfileName='StockSentiment-EC2InstanceProfile',
        RoleName='StockSentiment-EC2Role'
    )
    print("Created instance profile 'StockSentiment-EC2InstanceProfile'.")

# Lambda Execution Role
lambda_trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}

try:
    iam.get_role(RoleName='StockSentiment-LambdaRole')
    print("Role 'StockSentiment-LambdaRole' already exists.")
except Exception:
    iam.create_role(
        RoleName='StockSentiment-LambdaRole',
        AssumeRolePolicyDocument=json.dumps(lambda_trust_policy),
        Description='IAM Role for Stock Sentiment Lambda Stream Processor'
    )
    print("Created IAM Role 'StockSentiment-LambdaRole'.")

# Attach policy to Lambda Role
lambda_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetRecords",
                "dynamodb:GetShardIterator",
                "dynamodb:DescribeStream",
                "dynamodb:ListStreams"
            ],
            "Resource": f"arn:aws:dynamodb:{REGION}:{ACCOUNT_ID}:table/StockSentiment-LiveFeed/stream/*"
        },
        {
            "Effect": "Allow",
            "Action": ["cloudwatch:PutMetricData"],
            "Resource": "*"
        }
    ]
}
iam.put_role_policy(
    RoleName='StockSentiment-LambdaRole',
    PolicyName='StockSentiment-LambdaStreamPolicy',
    PolicyDocument=json.dumps(lambda_policy)
)
print("Attached policy to 'StockSentiment-LambdaRole'.")

print("\n=== Security Groups & IAM Roles Setup Completed Successfully! ===")
