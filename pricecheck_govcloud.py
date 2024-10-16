import boto3
import json
import os

def get_pricing_info(pricing_client, filters):
    response = pricing_client.get_products(
        ServiceCode='AmazonEC2',
        Filters=filters
    )
    print(f"Number of items in PriceList: {len(response['PriceList'])}")
    return response['PriceList']

def print_govcloud_pricing_info(price_list):
    for price_item in price_list:
        price_data = json.loads(price_item)
        attributes = price_data['product']['attributes']
        location = attributes.get('location', 'N/A')

        # Filter for GovCloud locations
        if "AWS GovCloud" in location:
            volume_api_name = attributes.get('volumeApiName', 'N/A')
            storage_media = attributes.get('storageMedia', 'N/A')

            # Extract pricePerUnit for OnDemand terms (USD)
            on_demand_terms = price_data.get('terms', {}).get('OnDemand', {})
            price_per_unit = None
            for term_key, term_value in on_demand_terms.items():
                price_dimensions = term_value.get('priceDimensions', {})
                for dimension_key, dimension_value in price_dimensions.items():
                    price_per_unit = dimension_value.get('pricePerUnit', {}).get('USD', 'N/A')

            print(f"Region: {location}")
            print(f"Volume API Name: {volume_api_name}")
            print(f"Storage Media: {storage_media}")
            print(f"Price per Unit (USD): {price_per_unit}")
            print("--------------------")
#1008            
def ensure_table_exists(dydb_client, table_name):
    # Check if the table exists
    try:
        response = dydb_client.describe_table(TableName=table_name)
        print(f"Table {table_name} already exists.")
    except ClientError as e:
        # Check if the error is that the table doesn't exist
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            # If the table does not exist, create it
            try:
                table = dydb_client.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {
                            'AttributeName': 'Account',  # Partition key
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'region',  # Sort key
                            'KeyType': 'RANGE'
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'Account',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'region',
                            'AttributeType': 'S'
                        }
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                print(f"Table {table_name} created successfully.")
                # Wait until the table exists
                dydb_client.get_waiter('table_exists').wait(TableName=table_name)
            except ClientError as e:
                print(f"Error creating table: {e}")
        else:
            print(f"Error describing table: {e}")

def main(aws_access_key_id, aws_secret_access_key, aws_session_token=None):
    try:
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name='us-east-1'
        )
        
        pricing_client = session.client('pricing')
        print("Successfully created pricing client.")

        # Query for gp2 volumes without GovCloud filter
        print("\nQuerying for gp2 volumes without GovCloud filter:")
        gp2_filters = [
            {'Type': 'TERM_MATCH', 'Field': 'volumeApiName', 'Value': 'gp2'},
            {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Storage'}
        ]
        gp2_price_list = get_pricing_info(pricing_client, gp2_filters)

        # Print GovCloud-specific pricing information from the result
        print("\nFiltering and printing GovCloud pricing information from gp2 results:")
        print_govcloud_pricing_info(gp2_price_list)

    except Exception as e:
        print(f"An error occurred: {str(e)}")


import boto3

def store_savings(account, volume_size, region, com_pricing, dydb_client, vol_savings_table):
    try:
        # Fetch the current size and savings for the tenant (account) using client
        response = dydb_client.get_item(
            TableName=vol_savings_table,
            Key={
                'Account': {'S': account},  # Partition key
                'Region': {'S': region}  # Sort key (if applicable)
            }
        )
        
        if 'Item' in response:
            # Previous saved size and savings exist, get the values
            previous_size = int(response['Item']['Size']['N'])  # Size is stored as a number
            previous_savings = float(response['Item']['Savings']['N'])  # Savings is stored as a number
        else:
            # No previous data, initialize to 0
            previous_size = 0
            previous_savings = 0.0
        
        # Get the cost per GB in this region
        volume_cost_per_gb = com_pricing[region]
        
        # Calculate the savings for the current volume size (not cumulative yet)
        current_run_savings = volume_size * volume_cost_per_gb
        
        # Update the total size after calculating the savings for the current run
        total_size = previous_size + volume_size
        
        # Add current run savings to the previous total savings
        total_savings = previous_savings + current_run_savings
        
        # Update the table with the new total size and total cumulative savings using put_item
        dydb_client.put_item(
            TableName=vol_savings_table,
            Item={
                'Account': {'S': account},   # Partition key
                'Region': {'S': region},     # Sort key (if applicable)
                'Size': {'N': str(total_size)},    # Total size of deleted volumes
                'Savings': {'N': str(total_savings)}  # Total cumulative savings
            }
        )
        
        print(f"Updated cumulative savings for account {account} in region {region}: {total_savings} USD")
        return total_savings
        
    except dydb_client.exceptions.ClientError as e:
        print(f"Failed to update DynamoDB: {e.response['Error']['Message']}")
        return None

# Example usage
govcloud_session = boto3.Session()  # Replace with your actual session initialization
dydb_client = govcloud_session.client('dynamodb')
vol_savings_table = 'volumesavingtracker'

account = '123456789012'
volume_size = 50
region = 'us-east-1'
com_pricing = {'us-east-1': 0.10}  # Example cost per GB

# store_savings(account, volume_size, region, com_pricing, dydb_client, vol_savings_table)



if __name__ == "__main__":
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_session_token = os.environ.get('AWS_SESSION_TOKEN')

    if not aws_access_key_id or not aws_secret_access_key:
        print("AWS credentials not found in environment variables.")
        print("Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
        print("If you're using temporary credentials, also set AWS_SESSION_TOKEN.")
        exit(1)
    
    print("AWS credentials found in environment variables.")
    main(aws_access_key_id, aws_secret_access_key, aws_session_token)
