import boto3
import os

REGION = "ap-south-1"
AMI_ID = "ami-0324b92f52e4d7a4a"  # Amazon Linux 2023 (ap-south-1)
INSTANCE_TYPE = "t3.micro"
SG_NAME = "StockSentiment-EC2-SG"
IAM_PROFILE_NAME = "StockSentiment-EC2InstanceProfile"

ec2 = boto3.client('ec2', region_name=REGION)

print("Checking EC2 instances for Stock Sentiment Analyser...")
instances = ec2.describe_instances(
    Filters=[
        {'Name': 'tag:Name', 'Values': ['StockSentiment-Dashboard-Worker']},
        {'Name': 'instance-state-name', 'Values': ['pending', 'running', 'stopped']}
    ]
)['Reservations']

if instances and instances[0]['Instances']:
    inst = instances[0]['Instances'][0]
    print(f"Instance already exists: ID={inst['InstanceId']}, State={inst['State']['Name']}, IP={inst.get('PublicIpAddress', 'None')}")
else:
    print(f"Fetching Security Group '{SG_NAME}'...")
    sgs = ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [SG_NAME]}])['SecurityGroups']
    sg_id = sgs[0]['GroupId']

    with open('aws/ec2_user_data.sh', 'r') as f:
        user_data = f.read()

    print(f"Launching EC2 instance ({INSTANCE_TYPE})...")
    resp = ec2.run_instances(
        ImageId=AMI_ID,
        InstanceType=INSTANCE_TYPE,
        MinCount=1,
        MaxCount=1,
        SecurityGroupIds=[sg_id],
        IamInstanceProfile={'Name': IAM_PROFILE_NAME},
        UserData=user_data,
        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': [
                {'Key': 'Name', 'Value': 'StockSentiment-Dashboard-Worker'},
                {'Key': 'Project', 'Value': 'StockSentimentAnalyser'}
            ]
        }]
    )
    new_inst = resp['Instances'][0]
    print(f"Launched EC2 instance successfully! InstanceId: {new_inst['InstanceId']}")
