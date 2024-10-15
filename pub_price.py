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
        for product in products.values():
            if product['productFamily'] == product_family:
                sku = product['sku']
                attributes = product['attributes']
                volume_type = attributes.get('volumeType', 'Unknown')
                
                if sku in data['terms']['OnDemand']:
                    price_dimensions = next(iter(data['terms']['OnDemand'][sku].values()))['priceDimensions']
                    price = next(iter(price_dimensions.values()))['pricePerUnit']['USD']
                    volume_prices[volume_type] = float(price)
        
        return volume_prices
    else:
        print(f"Error: Unable to fetch pricing data. Status code: {response.status_code}")
        return None

# Get pricing for us-gov-west-1 and us-gov-east-1
regions = ['us-gov-west-1', 'us-gov-east-1']

for region in regions:
    prices = get_aws_pricing(region)
    if prices:
        print(f"Volume prices for {region}:")
        for volume_type, price in prices.items():
            print(f"  {volume_type}: ${price} per GB-month")
    print()