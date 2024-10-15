import requests
import json

# AWS Pricing API URL for EBS
url = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEBS/current/index.json"

# Fetch the pricing data
response = requests.get(url)
pricing_data = response.json()

# Filter for gp2 pricing
gp2_pricing = []

for sku, product_info in pricing_data['products'].items():
    if product_info['productFamily'] == 'Storage' and 'gp2' in product_info['attributes'].get('volumeApiName', ''):
        # Extract price information
        for term in pricing_data['terms']['OnDemand'].get(sku, {}).values():
            for price_dimension in term['priceDimensions'].values():
                price_per_gb = price_dimension['pricePerUnit']['USD']
                region = product_info['attributes'].get('location')
                gp2_pricing.append({
                    'region': region,
                    'price_per_gb': price_per_gb
                })

# Display gp2 pricing
for price_info in gp2_pricing:
    print(f"Region: {price_info['region']}, Price per GB: {price_info['price_per_gb']}")
