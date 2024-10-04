import boto3
import json
import os

# Function to query EC2 pricing from the commercial AWS region
def get_pricing_info(pricing_client, filters):
    response = pricing_client.get_products(
        ServiceCode='AmazonEC2',
        Filters=filters
    )
    print(f"Number of items in PriceList: {len(response['PriceList'])}")
    return response['PriceList']

# Function to store data in DynamoDB in GovCloud
def store_in_dynamodb(dynamodb_client, table_name, volume_api_name, storage_media, price_per_unit, location):
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
            store_in_dynamodb(dynamodb_client, table_name, volume_api_name, storage_media, price_per_unit, location)

def main(aws_access_key_id, aws_secret_access_key, aws_session_token=None):
    try:
        # Create a session for the commercial AWS region (for pricing API calls)
        commercial_session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name='us-east-1'  # Commercial AWS region
        )
        
        # Create a session for GovCloud (for DynamoDB operations)
        govcloud_session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name='us-gov-west-1'  # GovCloud region
        )
        
        pricing_client = commercial_session.client('pricing')
        dynamodb_client = govcloud_session.client('dynamodb')

        table_name = "VolumePricing"  # Ensure this table exists in your DynamoDB GovCloud instance

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