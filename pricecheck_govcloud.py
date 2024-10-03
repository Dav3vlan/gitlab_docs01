import boto3
import json
import os

def get_gp2_pricing_govcloud(aws_access_key_id, aws_secret_access_key, aws_session_token=None):
    # Initialize the pricing client with provided credentials
    # Note: We're using 'us-east-1' for the pricing API, but we'll filter for GovCloud prices
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        region_name='us-east-1'
    )
    
    pricing_client = session.client('pricing')

    # Get the pricing for gp2 volumes, filtering for GovCloud
    response = pricing_client.get_products(
        ServiceCode='AmazonEC2',
        Filters=[
            {'Type': 'TERM_MATCH', 'Field': 'volumeApiName', 'Value': 'gp2'},
            {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Storage'},
            {'Type': 'TERM_MATCH', 'Field': 'locationType', 'Value': 'AWS GovCloud (US)'}
        ]
    )

    # Parse and print the pricing information
    for price_item in response['PriceList']:
        price_data = json.loads(price_item)
        
        # Extract relevant information
        location = price_data['product']['attributes']['location']
        storage_media = price_data['product']['attributes']['storageMedia']
        
        # Get the price per GB-month
        on_demand_pricing = price_data['terms']['OnDemand']
        price_dimensions = next(iter(on_demand_pricing.values()))['priceDimensions']
        price_dimension = next(iter(price_dimensions.values()))
        
        # Handle potential variations in currency
        price_per_unit = price_dimension['pricePerUnit']
        currency, amount = next(iter(price_per_unit.items()))
        
        # Get the price unit
        price_unit = price_dimension.get('unit', 'GB-Mo')
        
        print(f"Region: {location}")
        print(f"Storage Media: {storage_media}")
        print(f"Price per {price_unit}: {currency} {amount}")
        print("--------------------")

if __name__ == "__main__":
    # Retrieve AWS credentials from environment variables
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_session_token = os.environ.get('AWS_SESSION_TOKEN')

    if not aws_access_key_id or not aws_secret_access_key:
        print("AWS credentials not found in environment variables.")
        print("Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
        print("If you're using temporary credentials, also set AWS_SESSION_TOKEN.")
        exit(1)

    get_gp2_pricing_govcloud(aws_access_key_id, aws_secret_access_key, aws_session_token)
