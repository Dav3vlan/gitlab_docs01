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
                    volume_type = volume_api_name  # Use gp2 or gp3 instead of General Purpose
                
                if sku in data['terms']['OnDemand']:
                    price_dimensions = next(iter(data['terms']['OnDemand'][sku].values()))['priceDimensions']
                    price = next(iter(price_dimensions.values()))['pricePerUnit']['USD']
                    volume_prices[volume_type] = float(price)
        
        return volume_prices, gp_types
    else:
        print(f"Error: Unable to fetch pricing data. Status code: {response.status_code}")
        return None, None

def get_volume_price(region, volume_type):
    """
    Fetches the price per GB-month or IOPS for a specific volume type in a given AWS region.
    
    Parameters:
    region (str): AWS region (e.g., 'us-gov-west-1')
    volume_type (str): Volume type (e.g., 'gp2', 'gp3', 'Provisioned IOPS')
    
    Returns:
    float: Price per GB-month or IOPS, or None if not found
    """
    base_url = 'https://pricing.us-east-1.amazonaws.com'
    service_url = f'{base_url}/offers/v1.0/aws/AmazonEC2/current/{region}/index.json'
    
    try:
        response = requests.get(service_url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        
        data = response.json()
        products = data.get('products', {})
        
        for product in products.values():
            attributes = product.get('attributes', {})
            current_volume_type = attributes.get('volumeApiName', attributes.get('volumeType', 'Unknown'))
            
            # Handle specific cases where the naming might differ (e.g., IOPS volumes)
            if volume_type in ['gp2', 'gp3', 'Cold HDD', 'Throughput Optimized HDD', 'Magnetic']:
                match = (current_volume_type == volume_type)
            elif volume_type == 'Provisioned IOPS':
                match = (current_volume_type == 'io1' or current_volume_type == 'Provisioned IOPS')
            else:
                match = (current_volume_type == volume_type)

            # Check if the product matches the requested volume type
            if match:
                sku = product['sku']
                
                # Check if On-Demand pricing is available for the product
                if sku in data['terms']['OnDemand']:
                    on_demand_terms = data['terms']['OnDemand'][sku]
                    
                    # Loop through each term to find the correct unit price (GB-month or IOPS)
                    for term_value in on_demand_terms.values():
                        price_dimensions = term_value.get('priceDimensions', {})
                        for dimension_value in price_dimensions.values():
                            # For IOPS, the unit might be different (e.g., per IOPS-month)
                            if volume_type == 'Provisioned IOPS':
                                if dimension_value.get('unit') == 'IOPS-Mo':
                                    price = dimension_value['pricePerUnit'].get('USD', 'N/A')
                                    return float(price)
                            else:
                                # Ensure it's the correct unit of measure (GB-month for others)
                                if dimension_value.get('unit') == 'GB-Mo':
                                    price = dimension_value['pricePerUnit'].get('USD', 'N/A')
                                    return float(price)
        
        # If no matching product is found
        return None
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching pricing data: {e}")
        return None
# all of em
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
    
# Single call
region = 'us-gov-west-1'
volume_type = 'gp3'  # You can change this to 'gp3', 'gp2', etc.

price = get_volume_price(region, volume_type)
if price is not None:
    print(f"The price for {volume_type} in {region} is: ${price} per GB-month") # or IOPS-month")
else:
    print(f"No pricing found for {volume_type} in {region}")
