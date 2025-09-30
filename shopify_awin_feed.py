import csv
import requests
import os
import re
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Shopify API credentials from environment variables
SHOPIFY_API_KEY = os.getenv('SHOPIFY_API_KEY')
SHOPIFY_PASSWORD = os.getenv('SHOPIFY_PASSWORD')
SHOPIFY_STORE = os.getenv('SHOPIFY_STORE')

# Full AWIN CSV column headers (your current list)
AWIN_HEADERS = [
    'product_id', 'merchant_category', 'price', 'brand_name', 'upc', 'ean', 'mpn', 'isbn', 'model_number', 'product_name',
    'description', 'specifications', 'promotional_text', 'language', 'deep_link', 'merchant_thumb', 'image_url', 'delivery_time',
    'valid_from', 'valid_to', 'currency', 'delivery_cost', 'web_offer', 'pre_order', 'in_stock', 'stock_quantity', 'is_for_sale',
    'warranty', 'condition', 'product_type', 'parent_product_id', 'commission_group', 'last_updated', 'dimensions', 'colour',
    'keywords', 'custom1', 'custom2', 'custom3', 'custom4', 'custom5', 'saving', 'delivery_restrictions', 'reviews',
    'average_rating', 'rating', 'alternate_image', 'large_image', 'basket_link'
]

# Define category mapping
CATEGORY_MAP = {
    "Dresses": "Apparel & Accessories > Clothing > Dresses",
    "Tops": "Apparel & Accessories > Clothing > Shirts & Tops",
    "Sweater": "Apparel & Accessories > Clothing > Sweaters",
    "Pants": "Apparel & Accessories > Clothing > Pants",
    "Skirts": "Apparel & Accessories > Clothing > Skirts",
    "Accessories": "Apparel & Accessories > Clothing Accessories",
    "Scarves": "Apparel & Accessories > Clothing Accessories > Scarves",
    "Jewelry": "Apparel & Accessories > Jewelry",
    "": "Apparel & Accessories > Miscellaneous",   # fallback for empty product_type
}


# Minimal AWIN-required headers
AWIN_MINIMAL_HEADERS = [
    'product_id',
    'product_name',
    'description',
    'deep_link',
    'price',
    'currency',
    'brand_name',
    'merchant_category',
    'image_url',
    'in_stock',
    'stock_quantity'
]

# Use latest stable Shopify API version and authenticate with X-Shopify-Access-Token header
BASE_URL = f'https://{SHOPIFY_STORE}/admin/api/2024-01/products.json?limit=250&status=active'

def fetch_shopify_products():
    url = BASE_URL
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_PASSWORD,
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    products = response.json().get('products', [])
    return products

def write_shopify_csv(filename, products):
    if not products:
        print('No products to write to Shopify data CSV.')
        return
    all_keys = set()
    for product in products:
        all_keys.update(product.keys())
    all_keys = list(all_keys)
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=all_keys)
        writer.writeheader()
        for product in products:
            writer.writerow(product)

def clean_html(raw_html):
    """Remove HTML tags from Shopify description."""
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html or '').strip()

def format_for_awin(products):
    awin_rows = []
    for product in products:
        if not product.get('variants'):
            continue

        variant = product['variants'][0]
        price = variant.get('price')
        sku = variant.get('sku', '').strip()

        if not price or not sku:
            continue

        images = product.get('images', [])
        image_url = images[0]['src'] if images else (product['image']['src'] if product.get('image') else '')
        alternate_image = images[1]['src'] if len(images) > 1 else ''
        large_image = ''
        if images:
            large = max(images, key=lambda img: img.get('width', 0) * img.get('height', 0))
            large_image = large.get('src', '')

         # Map product_type to AWIN-friendly category
        raw_category = product.get('product_type', '').strip()
        category = CATEGORY_MAP.get(raw_category, "Apparel & Accessories > Miscellaneous")
        brand = product.get('vendor') or "Generic"
        description = clean_html(product.get('body_html', ''))

        row = {
            'product_id': sku,
            'merchant_category': category,
            'price': price,
            'brand_name': brand,
            'upc': variant.get('barcode', ''),
            'ean': '',
            'mpn': sku,
            'isbn': '',
            'model_number': '',
            'product_name': product.get('title', '').strip(),
            'description': description,
            'specifications': '',
            'promotional_text': '',
            'language': 'en_US',
            'deep_link': f"https://www.sarahalexis.com/products/{product.get('handle', '')}",
            'merchant_thumb': product['image']['src'] if product.get('image') else '',
            'image_url': image_url,
            'delivery_time': '',
            'valid_from': product.get('published_at', ''),
            'valid_to': '',
            'currency': 'USD',
            'delivery_cost': '',
            'web_offer': variant.get('compare_at_price', ''),
            'pre_order': '',
            'in_stock': '1' if variant.get('inventory_quantity', 0) > 0 else '0',
            'stock_quantity': variant.get('inventory_quantity', 0),
            'is_for_sale': '1' if product.get('status', '') == 'active' else '0',
            'warranty': '',
            'condition': 'new',
            'product_type': category,
            'parent_product_id': '',
            'commission_group': '',
            'last_updated': product.get('updated_at', ''),
            'dimensions': '',
            'colour': '',
            'keywords': product.get('tags', ''),
            'custom1': '',
            'custom2': '',
            'custom3': '',
            'custom4': '',
            'custom5': '',
            'saving': '',
            'delivery_restrictions': '',
            'reviews': '',
            'average_rating': '',
            'rating': '',
            'alternate_image': alternate_image,
            'large_image': large_image,
            'basket_link': f"https://www.sarahalexis.com/products/{product.get('handle', '')}",
        }
        awin_rows.append(row)
    return awin_rows

def write_csv(filename, rows, headers):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            # Keep only the keys that exist in headers
            writer.writerow({h: row.get(h, '') for h in headers})

def main():
    products = fetch_shopify_products()
    write_shopify_csv('shopify_data.csv', products)

    awin_rows = format_for_awin(products)

    # Write full feed
    write_csv('awin_full_feed.csv', awin_rows, AWIN_HEADERS)
    # Write minimal feed
    write_csv('awin_minimal_feed.csv', awin_rows, AWIN_MINIMAL_HEADERS)

    print('Shopify data saved: shopify_data.csv')
    print('AWIN full feed generated: awin_full_feed.csv')
    print('AWIN minimal feed generated: awin_minimal_feed.csv')

if __name__ == '__main__':
    main()