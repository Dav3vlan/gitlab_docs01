import boto3
import json
import os
import random
import string
import time
import random

# Function to generate a timestamp-based ID with a random component
def generate_timestamp_based_id():
    timestamp = int(time.time() * 1000)  # Current time in milliseconds
    random_number = random.randint(1000, 9999)  # 4-digit random number
    return f"{timestamp}-{random_number}"


if not gov_aws_session_token:
        print("GovCloud session token is missing. Please set it to proceed.")
        return
    
    # Validate Commercial session token
if not aws_session_token:
      print("Commercial AWS session token is missing. Please set it to proceed.")
      return
    
def validate_session_token(session):
    try:
        sts_client = session.client('sts')
        identity = sts_client.get_caller_identity()
        print(f"Token is valid. Account: {identity['Account']}, ARN: {identity['Arn']}")
        return True
    except Exception as e:
        print(f"Error validating session token: {str(e)}")
        return False

# Function to query EC2 pricing from the commercial AWS region
def get_pricing_info(pricing_client, filters):
    response = pricing_client.get_products(
        ServiceCode='AmazonEC2',
        Filters=filters
    )
    print(f"Number of items in PriceList: {len(response['PriceList'])}")
    return response['PriceList']

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


# Function to store data in DynamoDB in GovCloud
def store_in_dynamodb(dynamodb_client, table_name, volume_id, account_id, volume_api_name, storage_media, price_per_unit, location):
    try:
        response = dynamodb_client.put_item(
            TableName=table_name,
            Item={
                'VolumeApiName': {'S': volume_api_name},
                'StorageMedia': {'S': storage_media},
                'PricePerUnit': {'S': str(price_per_unit)},
                'Location': {'S': location}
            }
        )
        print(f"Data inserted successfully for {volume_api_name} in {location}")
    except Exception as e:
        print(f"Error storing data in DynamoDB: {str(e)}")

def store_or_update_in_dynamodb(dynamodb_client, table_name, volume_id, account_id, volume_api_name, storage_media, price_per_unit, location):
    try:
        response = dynamodb_client.update_item(
            TableName=table_name,
            Key={
                'VolumeId': {'S': volume_id},
                'AccountId': {'S': account_id}
            },
            UpdateExpression="SET VolumeApiName = :volume_api_name, StorageMedia = :storage_media, PricePerUnit = :price_per_unit, Location = :location",
            ExpressionAttributeValues={
                ':volume_api_name': {'S': volume_api_name},
                ':storage_media': {'S': storage_media},
                ':price_per_unit': {'S': str(price_per_unit)},
                ':location': {'S': location}
            },
            ReturnValues="UPDATED_NEW"
        )
        print(f"Data inserted or updated successfully for {volume_api_name} in {location} with VolumeId {volume_id}")
    except Exception as e:
        print(f"Error storing or updating data in DynamoDB: {str(e)}")

# Function to filter and store GovCloud pricing info in DynamoDB
def print_and_store_govcloud_pricing_info(price_list, dynamodb_client, table_name):
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

            # Store the data in DynamoDB
            ensure_table_exists(dynamo_client, table_name)
            volume_id = generate_timestamp_based_id()
            account_id = generate_timestamp_based_id()
            store_in_dynamodb(dynamodb_client, table_name, volume_id, account_id, volume_api_name, storage_media, price_per_unit, location)
def generate_random_id(length=8):
     characters = string.ascii_letters + string.digits
     return ''.join(random.choice(characters) for _ in range(length))
#1008    
def get_govcloud_pricing_info(price_list):
    pricing_info = []  # List to store location and price_per_unit data

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

            # Add the location and price_per_unit to the pricing_info list
            pricing_info.append({'location': location, 'price_per_unit': price_per_unit})

    return pricing_info  # Return the list of pricing information
    
    # for pricing_item in govcloud_pricing_info:
    #     location = pricing_item['location']
    #     price_per_unit = pricing_item['price_per_unit']
    #     print(f"Location: {location}, Price per Unit: {price_per_unit}")

#1009
def ensure_vol_savings_table(table_name, region):
    """
    Check if the specified DynamoDB table exists, and create it if it doesn't.
    
    :param table_name: Name of the DynamoDB table
    :param region: AWS region
    :return: True if the table exists or was created successfully, False otherwise
    """
    dynamodb = boto3.resource('dynamodb', region_name=region)
    
    try:
        table = dynamodb.Table(table_name)
        table.load()
        logger.info(f"Table {table_name} already exists.")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.info(f"Table {table_name} does not exist. Creating it now...")
            try:
                table = dynamodb.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {
                            'AttributeName': 'AccountId',
                            'KeyType': 'HASH'
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'AccountId',
                            'AttributeType': 'S'
                        }
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                table.wait_until_exists()
                logger.info(f"Table {table_name} created successfully.")
                return True
            except ClientError as create_error:
                logger.error(f"Error creating table: {create_error}")
                return False
        else:
            logger.error(f"Unexpected error: {e}")
            return False

def track_volume_savings(account, size, region):
    """
    Track the savings for each tenant by storing and updating volume sizes in DynamoDB.
    :param account: AWS account ID (tenant)
    :param size: Size of the gp2 volume being deleted (in GB)
    :param region: AWS region of the volume
    :return: Updated total savings for the account
    """
    
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name=region)
    table_name = 'VolumesSavingsTracker'
    
    # Check if the DynamoDB table exists
    try:
        table = dynamodb.Table(table_name)
        table.load()
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.error(f"Table {table_name} does not exist. Please create it first.")
            return None
        else:
            logger.error(f"Unexpected error: {e}")
            return None
    
    # Get the current savings value for the account
    try:
        response = table.get_item(Key={'AccountId': account})
    except ClientError as e:
        logger.error(f"Error retrieving item: {e}")
        return None
    
    current_savings = response.get('Item', {}).get('TotalSavings', 0)
    
    # Calculate new savings
    # Note: You'll need to implement a function to get the average volume cost for the region
    avg_volume_cost = get_average_volume_cost(region)  # Implement this function
    new_savings = current_savings + (size * avg_volume_cost)
    
    # Update the item in DynamoDB
    try:
        table.put_item(
            Item={
                'AccountId': account,
                'TotalSavings': new_savings
            }
        )
    except ClientError as e:
        logger.error(f"Error updating item: {e}")
        return None
    
    logger.info(f"Updated savings for account {account}: {new_savings}")
    return new_savings
    
def main(aws_access_key_id, aws_secret_access_key, aws_session_token=None):
    try:
        # Create a session for the commercial AWS region (for pricing API calls)
      
        # Generate random VolumeId and AccountId using alphanumeric strings
        volume_id = generate_random_id()  # Example: 'a8Kz3Nf2'
        account_id = generate_random_id()  # Example: '7jS5X9tB'
            
        commercial_session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name='us-east-1'  # Commercial AWS region
        )
        pricing_client = commercial_session.client('pricing')
        # Create a session for GovCloud (for DynamoDB operations)
        govcloud_session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name='us-gov-west-1'  # GovCloud region
        )

        # Validate the session token before proceeding
        if not validate_session_token(govcloud_session):
            print("Invalid GovCloud session token. Exiting.")
            return
        
        dynamodb_client = govcloud_session.client('dynamodb')
        table_name = "VolumePricing"

        print("Successfully created pricing client (Commercial) and DynamoDB client (GovCloud).")

        # Query for gp2 volumes without GovCloud filter
        print("\nQuerying for gp2 volumes in the commercial AWS region:")
        gp2_filters = [
            {'Type': 'TERM_MATCH', 'Field': 'volumeApiName', 'Value': 'gp2'},
            {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Storage'}
        ]
        gp2_price_list = get_pricing_info(pricing_client, gp2_filters)

        # Filter and store GovCloud-specific pricing information from the result
        print("\nFiltering and storing GovCloud pricing information from gp2 results:")
        print_and_store_govcloud_pricing_info(gp2_price_list, dynamodb_client, table_name)

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_session_token = os.environ.get('AWS_SESSION_TOKEN')
    gov_aws_access_key_id = os.environ.get('GOV_AWS_ACCESS_KEY_ID')
    gov_aws_secret_access_key = os.environ.get('GOV_AWS_SECRET_ACCESS_KEY')
    gov_aws_session_token = os.environ.get('GOV_AWS_SESSION_TOKEN')

    if not aws_access_key_id or not aws_secret_access_key:
        print("AWS credentials not found in environment variables.")
        print("Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
        print("If you're using temporary credentials, also set AWS_SESSION_TOKEN.")
        exit(1)
    
    
    print("AWS credentials found in environment variables.")
    main(aws_access_key_id, aws_secret_access_key, aws_session_token, gov_aws_access_key_id,gov_aws_secret_access_key,gov_aws_session_token)
