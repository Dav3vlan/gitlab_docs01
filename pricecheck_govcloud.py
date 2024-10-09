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


def store_savings(account, volume_size, region, com_pricing, table):
    try:
        # Fetch the current size for the tenant (account)
        response = table.get_item(Key={'Account': account})
        
        if 'Item' in response:
            # Previous saved size exists, get the value
            previous_size = response['Item']['Size']
        else:
            # No previous data, initialize to 0
            previous_size = 0
        
        # Add the current volume size to the previous size
        total_size = previous_size + volume_size
        
        # Get the cost per GB in this region
        volume_cost_per_gb = com_pricing[region]
        
        # Calculate the savings (total size * cost per GB)
        savings = total_size * volume_cost_per_gb
        
        # Update the table with the new size and savings
        table.put_item(
            Item={
                'Account': account,
                'Size': total_size,
                'Savings': savings
            }
        )
        
        print(f"Updated savings for account {account}: {savings} USD")
        return savings
        
    except ClientError as e:
        print(f"Failed to update DynamoDB: {e.response['Error']['Message']}")
        return None


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
