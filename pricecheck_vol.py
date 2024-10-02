import boto3
import json

def get_gp2_pricing():
    # Initialize the pricing client
    pricing_client = boto3.client('pricing', region_name='us-east-1')

    # Get the pricing for gp2 volumes
    response = pricing_client.get_products(
        ServiceCode='AmazonEC2',
        Filters=[
            {'Type': 'TERM_MATCH', 'Field': 'volumeApiName', 'Value': 'gp2'},
            {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Storage'}
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
        price_per_unit = next(iter(price_dimensions.values()))['pricePerUnit']['USD']
        
        print(f"Region: {location}")
        print(f"Storage Media: {storage_media}")
        print(f"Price per GB-month: ${price_per_unit}")
        print("--------------------")

if __name__ == "__main__":
    get_gp2_pricing()
