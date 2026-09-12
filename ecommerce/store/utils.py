import requests
from store.models import Product, Category

def import_products():
    """Fetch products from FakeStoreAPI and save to DB"""
    response = requests.get('https://fakestoreapi.com/products')
    data = response.json()

    for item in data:
        category_name = item.get('category', 'Default')
        category, _ = Category.objects.get_or_create(name=category_name)

        Product.objects.update_or_create(
            title=item['title'],
            defaults={
                'description': item['description'],
                'price': item['price'],
                'image': item['image'],
                'category': category
            }
        )
    print("✅ Products imported successfully!")
