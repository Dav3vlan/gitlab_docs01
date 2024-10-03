import json
from botocore.exceptions import ClientError
from genericpath import exists
from tarfile import TarFile 
import time
from datetime import datetime, date, timedelta
import os
import csv
from unittest import result
import boto3
import logging
import concurrent.futures

current_date = date.today()

## define logging values
handler = logging.StreamHandler()
formatter = logging.Formatter('%(names)s - %(message)s')
logger = logging.getLogger(os.environ['function_name'])
handler.setFormatter(formatter)
logger.addHandle(handler)
logger.setLevel(logging.INFO)

# ------ Global -----#
#vars go here


def lambda_handler(event, context):
   #  stuff here. 

# ----------------------------------------

def process_volumes(account, cloud_regions, context, target_role, data):
    """
       Some text here leaving out for now.
    """


def get_volume_price(pricing_client, volume_type, region):
    filters = [
        {'Type': 'TERM_MATCH', 'Field': 'volumeApiName', 'Value': volume_type},
        {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Storage'},
        {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region}
    ]
    response = pricing_client.get_products(ServiceCode='AmazonEC2', Filters=filters)
    for price_item in response['PriceList']:
        price_data = json.loads(price_item)
        on_demand_terms = price_data.get('terms', {}).get('OnDemand', {})
        for term_value in on_demand_terms.values():
            price_dimensions = term_value.get('priceDimensions', {})
            for dimension_value in price_dimensions.values():
                return float(dimension_value.get('pricePerUnit', {}).get('USD', 0))
    return 0  # Return 0 if price not found

def ensure_table_exists(dynamo_client, table_name):
    try:
        dynamo_client.describe_table(TableName=table_name)
        print(f"Table {table_name} already exists.")
    except dynamo_client.exceptions.ResourceNotFoundException:
        print(f"Table {table_name} does not exist. Creating...")
        dynamo_client.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'VolumeId', 'KeyType': 'HASH'},
                {'AttributeName': 'AccountId', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'VolumeId', 'AttributeType': 'S'},
                {'AttributeName': 'AccountId', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        dynamo_client.get_waiter('table_exists').wait(TableName=table_name)
        print(f"Table {table_name} created successfully.")

def calculate_and_upload_cost_savings(data, pricing_client, dynamo_client, table_name='VolumeCostSavings'):
    ensure_table_exists(dynamo_client, table_name)
    
    for volume in data:
        # Assuming data structure: [name, id, account, region, size, type, create_time, target_date, excluded]
        volume_id = volume[1]
        account = volume[2]
        region = volume[3]
        size = int(volume[4])
        volume_type = volume[5]
        target_termination_date = volume[7]

        volume_price = get_volume_price(pricing_client, volume_type, region)
        cost_savings = size * volume_price * 30  # Estimated monthly savings

        # Upload to DynamoDB
        dynamo_client.put_item(
            TableName=table_name,
            Item={
                'VolumeId': {'S': volume_id},
                'AccountId': {'S': account},
                'Region': {'S': region},
                'CostSavings': {'N': str(cost_savings)},
                'TargetTerminationDate': {'S': target_termination_date}
            }
        )

    print(f"Cost savings data for {len(data)} volumes uploaded to DynamoDB table {table_name}.")


# Example usage in your main lambda_handler:
# def lambda_handler(event, context):
#     # ... (your existing code to process volumes and create 'data' list)
#     
#     if data:
#         report_name = f'orphaned_volumes-{current_date}'
#         schema = ["Volume Name", "Volume ID", "Account", "Region", "Size", "Type", "Creation Time", "Target Termination Date", "Excluded"]
#         report = write_csv(report_name, schema, data)
#         upload = push_to_s3(report_name, bucket)
#         
#         pricing_client = boto3.client('pricing', region_name='us-east-1')
#         dynamo_client = boto3.client('dynamodb')
#         calculate_and_upload_cost_savings(data, pricing_client, dynamo_client, 'MyVolumesCostSavings')
