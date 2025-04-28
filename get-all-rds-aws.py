import boto3
import pandas as pd
from datetime import datetime

aws_access_key_id = 'Insert you Access Key Here'
aws_secret_access_key = 'Insert your Secret Key Here'

session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

def assume_role(aws_account_number, role_name):
    sts_client = session.client('sts')
    response = sts_client.assume_role(
        RoleArn=f'arn:aws:iam::{aws_account_number}:role/{role_name}',
        RoleSessionName='AssumeRoleSession1'
    )
    return response['Credentials']

account_roles = {
    #Insert your account Id's and the roles that your iam user can assume to in key value pair for each account.
    #Example:
    # '1234567890': 'CLOUD_DB_ADMIN_ROLE',
    # '2345567890': 'CLOUD_DB_ADMIN_ROLE',
}

account_names = {
    #Inser account ID's and the names of the accounts in key value pair for each account.
    #Example:
    #'1234567890': 'DEV,
    #'2345567890': 'PROD',
}

timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
filename = f'rds_details_{timestamp}.xlsx'

data = []

for aws_account_number, role_name in account_roles.items():
    try:
        credentials = assume_role(aws_account_number, role_name)
        account_name = account_names[aws_account_number]
        rds_client = session.client('rds',
                                    aws_access_key_id=credentials['AccessKeyId'],
                                    aws_secret_access_key=credentials['SecretAccessKey'],
                                    aws_session_token=credentials['SessionToken'])
        rds_instances = rds_client.describe_db_instances()
        for instance in rds_instances['DBInstances']:
            tags = rds_client.list_tags_for_resource(ResourceName=instance['DBInstanceArn'])['TagList']
            instance_create_time = instance['InstanceCreateTime']
            instance_create_time = instance_create_time.replace(tzinfo=None)
            tag_dict = {tag['Key']: tag['Value'] for tag in tags}
            data_dict = {
                'Account': account_name,
                'Region': rds_client.meta.region_name,
                'DBInstanceIdentifier': instance['DBInstanceIdentifier'],
                'DBInstanceClass': instance['DBInstanceClass'],
                'Engine': instance['Engine'],
                'EngineVersion': instance['EngineVersion'],
                'DBInstanceStatus': instance['DBInstanceStatus'],
                'MasterUsername': instance['MasterUsername'],
                'Endpoint': instance['Endpoint']['Address'],
                'AllocatedStorage': instance['AllocatedStorage'],
                'InstanceCreateTime': instance_create_time,
                'VpcId': instance['DBSubnetGroup']['VpcId'],
                'StorageType': instance['StorageType'],
            }
            data_dict.update(tag_dict)
            data.append(data_dict)
    except Exception as e:
        print(f"Error getting RDS instances for account {aws_account_number}: {e}")

df = pd.DataFrame(data)
df.to_excel(filename, index=False)