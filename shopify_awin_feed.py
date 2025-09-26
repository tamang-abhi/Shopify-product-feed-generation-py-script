
import csv
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Shopify API credentials from environment variables
SHOPIFY_API_KEY = os.getenv('SHOPIFY_API_KEY')
SHOPIFY_PASSWORD = os.getenv('SHOPIFY_PASSWORD')
SHOPIFY_STORE = os.getenv('SHOPIFY_STORE')

# AWIN CSV column headers (example, adjust as needed)
AWIN_HEADERS = [
    'product_id', 'product_name', 'description', 'price', 'currency', 'product_url', 'image_url', 'category', 'brand', 'stock'
]


# Check for missing credentials and print clear error
if not SHOPIFY_API_KEY or not SHOPIFY_PASSWORD or not SHOPIFY_STORE:
    print("ERROR: One or more Shopify credentials are missing. Please check your .env file.")
    print(f"SHOPIFY_API_KEY: {'set' if SHOPIFY_API_KEY else 'MISSING'}")
    print(f"SHOPIFY_PASSWORD: {'set' if SHOPIFY_PASSWORD else 'MISSING'}")
    print(f"SHOPIFY_STORE: {'set' if SHOPIFY_STORE else 'MISSING'}")
    exit(1)


# Use latest stable Shopify API version and authenticate with X-Shopify-Access-Token header
BASE_URL = f'https://{SHOPIFY_STORE}/admin/api/2024-01/products.json?limit=250'

def fetch_shopify_products():
    url = BASE_URL
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_PASSWORD,
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get('products', [])

def format_for_awin(products):
    awin_rows = []
    for product in products:
        row = {
            'product_id': product['id'],
            'product_name': product['title'],
            'description': product.get('body_html', ''),
            'price': product['variants'][0]['price'],
            'currency': 'USD',  # Adjust as needed
            'product_url': f"https://{SHOPIFY_STORE}/products/{product['handle']}",
            'image_url': product['image']['src'] if product.get('image') else '',
            'category': product['product_type'],
            'brand': product.get('vendor', ''),
            'stock': product['variants'][0]['inventory_quantity'],
        }
        awin_rows.append(row)
    return awin_rows

def write_csv(filename, rows):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=AWIN_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def main():
    products = fetch_shopify_products()
    awin_rows = format_for_awin(products)
    write_csv('awin_product_feed.csv', awin_rows)
    print('AWIN product feed generated: awin_product_feed.csv')

if __name__ == '__main__':
    main()
