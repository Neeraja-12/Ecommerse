from django.core.management.base import BaseCommand
from store.models import Product, Category


CATEGORY_MAP = {
    "men's clothing": "Fashion",
    "women's clothing": "Fashion",
    "jewelery": "Fashion",
    "electronics": "Electronics",
}

# All products hardcoded so sync never depends on external API.
ALL_PRODUCTS = [
    # ---------- ELECTRONICS ----------
    {'id': 1, 'title': 'Fjallraven Backpack', 'price': 109.95, 'category': 'Electronics',
     'description': 'Your perfect pack for everyday use and walks in the forest.',
     'image': 'https://fakestoreapi.com/img/81fPKd-2AYL._AC_SL1500_.jpg'},
    {'id': 2, 'title': 'Mens Casual T-Shirt', 'price': 22.30, 'category': 'Fashion',
     'description': 'Slim-fitting style, contrast raglan long sleeve.',
     'image': 'https://fakestoreapi.com/img/71-3HjGNDUL._AC_SY879._SX._UX._SY._UY_.jpg'},
    {'id': 3, 'title': 'Mens Cotton Jacket', 'price': 55.99, 'category': 'Fashion',
     'description': 'Great outerwear jackets for Spring, Autumn, Winter.',
     'image': 'https://fakestoreapi.com/img/71li-ujtlUL._AC_UX679_.jpg'},
    {'id': 4, 'title': 'Mens Casual Slim Fit', 'price': 15.99, 'category': 'Fashion',
     'description': 'The color could be slightly different between on the screen and in practice.',
     'image': 'https://fakestoreapi.com/img/71YXzeOuslL._AC_UY879_.jpg'},
    {'id': 5, 'title': 'Gold Micrometer Bracelet', 'price': 695.00, 'category': 'Fashion',
     'description': 'Satisfaction Guaranteed. All our products are made with the finest materials.',
     'image': 'https://fakestoreapi.com/img/71pWzhdJNwL._AC_UL640_QL65_ML3_.jpg'},
    {'id': 6, 'title': 'Solid Gold Petite Micropave', 'price': 168.00, 'category': 'Fashion',
     'description': 'Satisfaction Guaranteed. Rose gold plated.',
     'image': 'https://fakestoreapi.com/img/61sbMiUnoGL._AC_UL640_QL65_ML3_.jpg'},
    {'id': 7, 'title': 'White Gold Plated Princess Ring', 'price': 9.99, 'category': 'Fashion',
     'description': 'Classic Created Wedding Engagement Solitaire Diamond Promise Ring.',
     'image': 'https://fakestoreapi.com/img/71YAIFU48IL._AC_UL640_QL65_ML3_.jpg'},
    {'id': 8, 'title': 'Pierced Owl Rose Gold Plated', 'price': 10.99, 'category': 'Fashion',
     'description': 'Rose Gold Plated Double Flared Tunnel Plug Earrings.',
     'image': 'https://fakestoreapi.com/img/51UDEzMJVpL._AC_UL640_QL65_ML3_.jpg'},

    # ---------- HARD DRIVES / MISC ----------
    {'id': 9, 'title': 'WD 2TB External Hard Drive', 'price': 64.00, 'category': 'Electronics',
     'description': 'USB 3.0 and USB 2.0 Compatibility Fast data transfers.',
     'image': 'https://fakestoreapi.com/img/61IBBVJvSDL._AC_SY879_.jpg'},
    {'id': 10, 'title': 'SanDisk SSD PLUS 1TB', 'price': 109.00, 'category': 'Electronics',
     'description': 'Easy upgrade for faster boot up, shutdown, application load and response.',
     'image': 'https://fakestoreapi.com/img/61U7T1koQqL._AC_SX679_.jpg'},
    {'id': 11, 'title': 'Silicon Power 256GB SSD', 'price': 109.00, 'category': 'Electronics',
     'description': '3D NAND flash are applied to deliver high transfer speeds.',
     'image': 'https://fakestoreapi.com/img/71kWymZ+c+L._AC_SX679_.jpg'},
    {'id': 12, 'title': 'WD 4TB Gaming Drive', 'price': 114.00, 'category': 'Electronics',
     'description': 'Expand your PS4 gaming experience, Play anywhere.',
     'image': 'https://fakestoreapi.com/img/61mtL65D4cL._AC_SX679_.jpg'},
    {'id': 13, 'title': 'Acer SB220Q 21.5 inches', 'price': 599.00, 'category': 'Electronics',
     'description': '21.5 inches Full HD (1920 x 1080) widescreen IPS display.',
     'image': 'https://fakestoreapi.com/img/81QpkIctqPL._AC_SX679_.jpg'},
    {'id': 14, 'title': 'Samsung 49-Inch Curved Gaming', 'price': 999.99, 'category': 'Electronics',
     'description': '49 inch super ultrawide 32:9 QLED gaming monitor.',
     'image': 'https://fakestoreapi.com/img/81Zt42ioCgL._AC_SX679_.jpg'},

    # ---------- WOMEN'S CLOTHING ----------
    {'id': 15, 'title': 'Women Snowboard Jacket', 'price': 56.99, 'category': 'Fashion',
     'description': 'Note: The Jackets is US standard size.',
     'image': 'https://fakestoreapi.com/img/51Y5NI-I5jL._AC_UX679_.jpg'},
    {'id': 16, 'title': 'Women Leather Jacket', 'price': 29.95, 'category': 'Fashion',
     'description': '100% Polyester; faux leather shell.',
     'image': 'https://fakestoreapi.com/img/81XH0e8fefL._AC_UY879_.jpg'},
    {'id': 17, 'title': 'Women Rain Jacket', 'price': 39.99, 'category': 'Fashion',
     'description': 'Lightweight perfect for trip or casual wear.',
     'image': 'https://fakestoreapi.com/img/71HblAHs5xL._AC_UY879_-2.jpg'},
    {'id': 18, 'title': 'Women Short Sleeve Boat Neck', 'price': 9.85, 'category': 'Fashion',
     'description': '95% rayon, 5% spandex. Casual short sleeve.',
     'image': 'https://fakestoreapi.com/img/71z3kpMAYsL._AC_UY879_.jpg'},
    {'id': 19, 'title': 'Women Slim Fit T-Shirt', 'price': 7.95, 'category': 'Fashion',
     'description': '100% cotton. Slim fit, short sleeve.',
     'image': 'https://fakestoreapi.com/img/51eg55uWmdL._AC_UX679_.jpg'},
    {'id': 20, 'title': 'Women Cotton Blouse', 'price': 12.95, 'category': 'Fashion',
     'description': '95% Cotton, 5% Spandex. Loose fit.',
     'image': 'https://fakestoreapi.com/img/61pHAEJ4NML._AC_UX679_.jpg'},

    # ---------- CUSTOM PRODUCTS ----------
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
    help = 'Sync all products into the database (no external API needed)'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for p in ALL_PRODUCTS:
            raw_cat = p.get('category', 'general')
            cat_name = CATEGORY_MAP.get(raw_cat, raw_cat.title())
            category, _ = Category.objects.get_or_create(name=cat_name)

            defaults = {
                'title': p['title'],
                'description': p.get('description', ''),
                'price': p['price'],
                'category': category,
                'in_stock': True,
                'stock_quantity': 50,
                'image': p.get('image', ''),
            }

            obj, created = Product.objects.update_or_create(
                id=p['id'],
                defaults=defaults,
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'✅ Synced {len(ALL_PRODUCTS)} products — {created_count} created, {updated_count} updated'
        ))