from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from store.models import Product, Category
import requests


CATEGORY_MAP = {
    "men's clothing": "Fashion",
    "women's clothing": "Fashion",
    "jewelery": "Fashion",
    "electronics": "Electronics",
}

CUSTOM_PRODUCTS = [
    {'id': 21, 'title': 'Stylish Hat', 'price': 25.99, 'category': 'Fashion',
     'description': 'Cool unisex fashion hat',
     'image': 'https://images.unsplash.com/photo-1521369909029-2afed882baee?w=500'},

    {'id': 22, 'title': 'Designer Watch', 'price': 150.00, 'category': 'Fashion',
     'description': 'Luxury stainless steel wristwatch',
     'image': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500'},

    {'id': 23, 'title': 'Leather Handbag', 'price': 110.50, 'category': 'Fashion',
     'description': 'Elegant premium leather handbag',
     'image': 'https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=500'},

    {'id': 31, 'title': 'Modern Lamp', 'price': 45.50, 'category': 'Home',
     'description': 'Stylish bedside lamp',
     'image': 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=500'},

    {'id': 32, 'title': 'Wooden Chair', 'price': 89.00, 'category': 'Home',
     'description': 'Comfortable oak chair',
     'image': 'https://images.unsplash.com/photo-1503602642458-232111445657?w=500'},

    {'id': 41, 'title': 'Python Programming', 'price': 30.00, 'category': 'Books',
     'description': 'Learn Python step-by-step',
     'image': 'https://images.unsplash.com/photo-1532012197267-da84d127e765?w=500'},

    {'id': 42, 'title': 'Django for Beginners', 'price': 35.00, 'category': 'Books',
     'description': 'A guide to Django web framework',
     'image': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500'},
]


class Command(BaseCommand):
    help = 'Sync products from FakeStoreAPI + custom list into the database'

    def handle(self, *args, **options):
        # ---- Step 1: Fetch from API ----
        try:
            resp = requests.get('https://fakestoreapi.com/products', timeout=10)
            api_products = resp.json() if resp.status_code == 200 else []
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'API failed: {e}'))
            api_products = []

        all_products = api_products + CUSTOM_PRODUCTS

        created_count = 0
        updated_count = 0

        for p in all_products:
            # Get or create category
            raw_cat = p.get('category', 'general')
            cat_name = CATEGORY_MAP.get(raw_cat, raw_cat.title())
            category, _ = Category.objects.get_or_create(name=cat_name)

            # Use API id as the primary key so URLs stay consistent
            product_id = p['id']

            defaults = {
                'title': p['title'],
                'description': p.get('description', ''),
                'price': p['price'],
                'category': category,
                'in_stock': True,
                'stock_quantity': 50,
                'image': p.get('image', ''),
            }

            product, created = Product.objects.update_or_create(
                id=product_id,
                defaults=defaults,
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'✅ Synced {len(all_products)} products — {created_count} created, {updated_count} updated'
        ))