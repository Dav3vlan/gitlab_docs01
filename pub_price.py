import requests
import json

def get_aws_pricing(region, service='AmazonEC2', product_family='Storage'):
    base_url = 'https://pricing.us-east-1.amazonaws.com'
    service_url = f'{base_url}/offers/v1.0/aws/{service}/current/{region}/index.json'
    
    response = requests.get(service_url)
    if response.status_code == 200:
        data = response.json()
        products = data['products']
        
        volume_prices = {}
        gp_types = set()
        
        for product in products.values():
            if product['productFamily'] == product_family:
                sku = product['sku']
                attributes = product['attributes']
                volume_type = attributes.get('volumeType', 'Unknown')
                volume_api_name = attributes.get('volumeApiName', '')
                
                if volume_type == 'General Purpose':
                    gp_types.add(volume_api_name)
                    volume_type = volume_api_name  # Use gp2 or gp3 instead of General Purpose.  
                
                if sku in data['terms']['OnDemand']: # Verify this asap. 
                    price_dimensions = next(iter(data['terms']['OnDemand'][sku].values()))['priceDimensions']
                    price = next(iter(price_dimensions.values()))['pricePerUnit']['USD']
                    volume_prices[volume_type] = float(price)
        
        return volume_prices, gp_types
    else:
        print(f"Error: Unable to fetch pricing data. Status code: {response.status_code}")
        return None, None

# Get pricing for us-gov-west-1 and us-gov-east-1
regions = ['us-gov-west-1', 'us-gov-east-1']

for region in regions:
    prices, gp_types = get_aws_pricing(region)
    if prices:
        print(f"Volume prices for {region}:")
        for volume_type, price in prices.items():
            print(f"  {volume_type}: ${price} per GB-month")
        
        if 'gp3' in gp_types and 'gp3' not in prices:
            print("  Note: gp3 volumes are available, but pricing is not explicitly provided in the API response.")
            print("  The gp3 base price is typically lower than gp2, but may have additional charges for IOPS and throughput.")
    print()
