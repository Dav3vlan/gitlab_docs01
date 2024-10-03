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

def print_pricing_info(price_list):
    for price_item in price_list:
        price_data = json.loads(price_item)
        attributes = price_data['product']['attributes']
        location = attributes.get('location', 'N/A')
        volume_api_name = attributes.get('volumeApiName', 'N/A')
        storage_media = attributes.get('storageMedia', 'N/A')
        
        print(f"Region: {location}")
        print(f"Volume API Name: {volume_api_name}")
        print(f"Storage Media: {storage_media}")
        print("--------------------")

def get_available_locations(pricing_client):
    response = pricing_client.get_attribute_values(
        ServiceCode='AmazonEC2',
        AttributeName='location'
    )
    return [attr['Value'] for attr in response['AttributeValues']]

def get_available_volume_types(pricing_client):
    response = pricing_client.get_attribute_values(
        ServiceCode='AmazonEC2',
        AttributeName='volumeApiName'
    )
    return [attr['Value'] for attr in response['AttributeValues']]

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

        # 1. Try to get gp2 pricing without GovCloud filter
        print("\nQuerying for gp2 volumes without GovCloud filter:")
        gp2_filters = [
            {'Type': 'TERM_MATCH', 'Field': 'volumeApiName', 'Value': 'gp2'},
            {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Storage'}
        ]
        gp2_price_list = get_pricing_info(pricing_client, gp2_filters)
        print_pricing_info(gp2_price_list)

        # 2. Get all available locations
        print("\nAvailable locations:")
        locations = get_available_locations(pricing_client)
        print(json.dumps(locations, indent=2))

        # 3. Get available volume types for GovCloud
        print("\nAvailable volume types:")
        volume_types = get_available_volume_types(pricing_client)
        print(json.dumps(volume_types, indent=2))

        # 4. Try to get any storage pricing for GovCloud
        print("\nQuerying for any storage in GovCloud:")
        govcloud_filters = [
            {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Storage'},
            {'Type': 'TERM_MATCH', 'Field': 'locationType', 'Value': 'AWS GovCloud (US)'}
        ]
        govcloud_price_list = get_pricing_info(pricing_client, govcloud_filters)
        print_pricing_info(govcloud_price_list)

    except Exception as e:
        print(f"An error occurred: {str(e)}")

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
