import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Product, Category
from decimal import Decimal

# Ensure categories exist
categories = {}
for name in ['fashion', 'home', 'books', 'electronics']:
    cat, created = Category.objects.get_or_create(name=name)
    categories[name] = cat
    if created:
        print('Created category: ' + name)

# The 6 products to add (Leather Handbag already exists)
products = [
    {'title': 'Stylish Hat', 'description': 'Cool unisex fashion hat', 'price': Decimal('25.99'), 'category': 'fashion', 'image': '/static/store/images/hat.jpg', 'sku': 'external-21'},
    {'title': 'Designer Watch', 'description': 'Luxury stainless steel wristwatch', 'price': Decimal('150.00'), 'category': 'fashion', 'image': '/static/store/images/watch.jpg', 'sku': 'external-22'},
    {'title': 'Modern Lamp', 'description': 'Stylish bedside lamp', 'price': Decimal('45.50'), 'category': 'home', 'image': '/static/store/images/lamp.jpg', 'sku': 'external-31'},
    {'title': 'Wooden Chair', 'description': 'Comfortable oak chair', 'price': Decimal('89.00'), 'category': 'home', 'image': '/static/store/images/chair.jpg', 'sku': 'external-32'},
    {'title': 'Python Programming', 'description': 'Learn Python step-by-step', 'price': Decimal('30.00'), 'category': 'books', 'image': '/static/store/images/python.jpg', 'sku': 'external-41'},
    {'title': 'Django for Beginners', 'description': 'A guide to Django web framework', 'price': Decimal('35.00'), 'category': 'books', 'image': '/static/store/images/django.jpg', 'sku': 'external-42'},
]

for p in products:
    cat = categories.get(p['category'])
    obj, created = Product.objects.update_or_create(
        sku=p['sku'],
        defaults={
            'title': p['title'],
            'description': p['description'],
            'price': p['price'],
            'category': cat,
            'image': p['image'],
            'in_stock': True,
            'stock_quantity': 10,
        }
    )
    if created:
        print('Created: ' + p['title'])
    else:
        print('Updated: ' + p['title'])

print('Done. Total products: ' + str(Product.objects.count()))
