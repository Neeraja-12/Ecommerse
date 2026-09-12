import requests
from store.models import Product, Category, categories, extra_products

def import_products():
    """Fetch products from FakeStoreAPI and save to DB"""
    try:
        response = requests.get('https://fakestoreapi.com/products')
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ Failed to fetch API data: {e}")
        return

    # Loop through each product and store with its category
    for item in data:
        category_name = item.get('category', 'Uncategorized').capitalize()
        category, _ = Category.objects.get_or_create(name=category_name)

        product, created = Product.objects.update_or_create(
            title=item['title'],
            defaults={
                'description': item['description'],
                'price': item['price'],
                'image': item['image'],
                'category': category
            }
        )

        action = "🆕 Created" if created else "🔁 Updated"
        print(f"{action}: {product.title}")

    print("✅ All products imported successfully!")

