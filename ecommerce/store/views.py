from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.core.paginator import Paginator
from django.core.cache import cache
from django.utils import timezone
from django.db import transaction
from django.contrib.sessions.backends.db import SessionStore
from .models import Category, Product, Cart, Order, OrderItem, OrderTracking
from django.db.models import Sum
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse,HttpResponse
from decimal import Decimal, ROUND_HALF_UP

import requests
import random
import string
from collections import Counter


from .models import UserAddress, Order, OrderItem

from .forms import AddressForm, CheckoutForm,CustomUserCreationForm,NewsletterForm


# ------------------ Helper utilities ------------------

def generate_tracking_number():
    """Generate a random tracking number."""
    letters = ''.join(random.choices(string.ascii_uppercase, k=4))
    numbers = ''.join(random.choices(string.digits, k=8))
    return f"TRK{letters}{numbers}"


# ------------------ Product helpers / caching ------------------

def get_custom_product(product_id):
    """Fallback custom products (used when API unavailable)."""
    custom_products = {
        '1': {'id': 1, 'title': 'Fjallraven Backpack', 'price': 109.95, 'category': "men's clothing", 'description': 'Your perfect pack for everyday use', 'image': 'https://fakestoreapi.com/img/81fPKd-2AYL._AC_SL1500_.jpg'},
        '2': {'id': 2, 'title': 'Mens Casual T-Shirt', 'price': 22.30, 'category': "men's clothing", 'description': 'Slim-fitting style', 'image': 'https://fakestoreapi.com/img/71-3HjGNDUL._AC_SY879._SX._UX._SY._UY_.jpg'},
        '3': {'id': 3, 'title': 'Mens Cotton Jacket', 'price': 55.99, 'category': "men's clothing", 'description': 'Great outerwear jackets', 'image': 'https://fakestoreapi.com/img/71li-ujtlUL._AC_UX679_.jpg'},
        '4': {'id': 4, 'title': 'Mens Casual Slim Fit', 'price': 15.99, 'category': "men's clothing", 'description': 'The color could be slightly different', 'image': 'https://fakestoreapi.com/img/71YXzeOuslL._AC_UY879_.jpg'},
        '5': {'id': 5, 'title': 'Gold Micrometer', 'price': 695.00, 'category': 'jewelery', 'description': 'Satisfaction Guaranteed', 'image': 'https://fakestoreapi.com/img/71pWzhdJNwL._AC_UL640_QL65_ML3_.jpg'},
        '21': {'id': 21, 'title': 'Stylish Hat', 'price': 25.99, 'category': 'fashion', 'description': 'Cool unisex fashion hat', 'image': '/static/store/images/hat.jpg'},
        '22': {'id': 22, 'title': 'Designer Watch', 'price': 150.00, 'category': 'fashion', 'description': 'Luxury stainless steel wristwatch', 'image': '/static/store/images/watch.jpg'},
        '23': {'id': 23, 'title': 'Leather Handbag', 'price': 110.50, 'category': 'fashion', 'description': 'Elegant premium leather handbag', 'image': '/static/store/images/handbag.jpg'},
        '31': {'id': 31, 'title': 'Modern Lamp', 'price': 45.50, 'category': 'home', 'description': 'Stylish bedside lamp', 'image': '/static/store/images/lamp.jpg'},
        '32': {'id': 32, 'title': 'Wooden Chair', 'price': 89.00, 'category': 'home', 'description': 'Comfortable oak chair', 'image': '/static/store/images/chair.jpg'},
        '41': {'id': 41, 'title': 'Python Programming', 'price': 30.00, 'category': 'books', 'description': 'Learn Python step-by-step', 'image': '/static/store/images/python.jpg'},
        '42': {'id': 42, 'title': 'Django for Beginners', 'price': 35.00, 'category': 'books', 'description': 'A guide to Django web framework', 'image': '/static/store/images/django.jpg'},
    }
    return custom_products.get(str(product_id))


def get_product_from_cache_or_api(product_id):
    """Try cache -> API -> custom product. Always returns a dict or None."""
    cache_key = f'product_{product_id}'
    product = cache.get(cache_key)

    if product:
        return product

    # Try remote API
    try:
        resp = requests.get(f'https://fakestoreapi.com/products/{product_id}', timeout=5)
        if resp.status_code == 200:
            product = resp.json()
            cache.set(cache_key, product, 3600)
            return product
    except requests.RequestException:
        # Fail silently and fallback
        pass

    # Fallback to custom products
    product = get_custom_product(product_id)
    if product:
        cache.set(cache_key, product, 3600)
    return product


def get_all_products():
    """Return combined product list from API + custom products (cached)."""
    cache_key = 'all_products'
    products = cache.get(cache_key)

    if products:
        return products

    products = []
    try:
        resp = requests.get('https://fakestoreapi.com/products', timeout=10)
        if resp.status_code == 200:
            products = resp.json()
    except requests.RequestException:
        products = []

    # Append custom products
    custom_products = [
        {'id': 21, 'title': 'Stylish Hat', 'price': 25.99, 'category': 'fashion', 'description': 'Cool unisex fashion hat', 'image': 'https://picsum.photos/200?random=1'},
        {'id': 22, 'title': 'Designer Watch', 'price': 150.00, 'category': 'fashion', 'description': 'Luxury stainless steel wristwatch', 'image': 'https://picsum.photos/200?random=1'},
        {'id': 23, 'title': 'Leather Handbag', 'price': 110.50, 'category': 'fashion', 'description': 'Elegant premium leather handbag', 'image': 'https://picsum.photos/200?random=1'},
        {'id': 31, 'title': 'Modern Lamp', 'price': 45.50, 'category': 'home', 'description': 'Stylish bedside lamp', 'image': 'https://picsum.photos/200?random=1'},
        {'id': 32, 'title': 'Wooden Chair', 'price': 89.00, 'category': 'home', 'description': 'Comfortable oak chair', 'image': 'https://picsum.photos/200?random=1'},
        {'id': 41, 'title': 'Python Programming', 'price': 30.00, 'category': 'books', 'description': 'Learn Python step-by-step', 'image': 'https://picsum.photos/200?random=1'},
        {'id': 42, 'title': 'Django for Beginners', 'price': 35.00, 'category': 'books', 'description': 'A guide to Django web framework', 'image': 'https://picsum.photos/200?random=1'},
    ]
    products.extend(custom_products)
    cache.set(cache_key, products, 1800)
    return products


# ------------------ Cart session helpers ------------------

def ensure_cart_session(request):
    """Guarantee there's a session and a 'cart' dict inside it."""
    if not request.session.session_key:
        request.session.create()
    if 'cart' not in request.session:
        request.session['cart'] = {'items': {}}
        request.session.modified = True
    return request.session['cart']

def save_cart_session(request):
    request.session.modified = True
    request.session.save()


def calculate_cart_totals(cart_items):
    if not cart_items:
        return {'subtotal': 0, 'shipping': 0, 'tax': 0, 'grand_total': 0}

    subtotal = sum(item.get('subtotal', 0) for item in cart_items)
    shipping = 0 if subtotal > 50 else 5.99
    tax = subtotal * 0.08
    grand_total = subtotal + shipping + tax

    return {
        'subtotal': round(subtotal, 2),
        'shipping': round(shipping, 2),
        'tax': round(tax, 2),
        'grand_total': round(grand_total, 2),
    }


def get_cart_data(request):
    """Return cart items with product info and totals."""
    cart = ensure_cart_session(request)
    cart_items = []
    failed = []

    for product_id, quantity in cart['items'].items():
        product = get_product_from_cache_or_api(product_id)
        if not product:
            failed.append(product_id)
            continue

        quantity = int(quantity)
        subtotal = float(product['price']) * quantity
        cart_items.append({
            'id': product_id,
            'title': product['title'],
            'price': float(product['price']),
            'image': product.get('image'),
            'quantity': quantity,
            'subtotal': round(subtotal, 2),
            'category': product.get('category', 'general')
        })

    # Remove failed products from session
    if failed:
        for pid in failed:
            cart['items'].pop(pid, None)
        save_cart_session(request)

    # Calculate totals
    subtotal = sum(item['subtotal'] for item in cart_items)
    shipping = 0 if subtotal >= 50 else 5.99
    tax = round(subtotal * 0.08, 2)
    grand_total = round(subtotal + shipping + tax, 2)
    total_quantity = sum(item['quantity'] for item in cart_items)
    shipping_remaining = max(0, 50 - subtotal)

    return {
        'cart_items': cart_items,
        'total_quantity': total_quantity,
        'total_price': subtotal,
        'shipping': shipping,
        'tax': tax,
        'grand_total': grand_total,
        'shipping_remaining': shipping_remaining,
    }

# ------------------ Views ------------------

def home(request):
    query = request.GET.get('q')
    category_filter = request.GET.get('category')

    # ✅ Get all database products (Admin added)
    db_products = list(Product.objects.filter(in_stock=True))

    # ✅ If you also use API products:
    try:
        api_products = get_all_products()  # only if you still want to keep API ones
    except requests.RequestException:
        api_products = []

    # Combine both lists
    all_products = []

    # Normalize db products to same structure as API
    for p in db_products:
        all_products.append({
            'id': p.id,
            'title': p.title,
            'price': float(p.discounted_price or p.price),
            'image': p.image or (p.local_image.url if p.local_image else ''),
            'category': p.category.name if p.category else 'general'
        })

    all_products += api_products  # merge both

    # Apply filters
    if query:
        all_products = [p for p in all_products if query.lower() in p['title'].lower()]
    if category_filter:
        all_products = [p for p in all_products if p.get('category', '').lower() == category_filter.lower()]

    paginator = Paginator(all_products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    categories_counter = Counter(p.get('category', 'general') for p in all_products)
    categories = [
        {'name': 'Electronics', 'slug': 'electronics', 'count': categories_counter.get('electronics', 0)},
        {'name': 'Fashion', 'slug': 'fashion', 'count': categories_counter.get('fashion', 0) + categories_counter.get('jewelery', 0) + categories_counter.get("men's clothing", 0) + categories_counter.get("women's clothing", 0)},
        {'name': 'Home', 'slug': 'home', 'count': categories_counter.get('home', 0)},
        {'name': 'Books', 'slug': 'books', 'count': categories_counter.get('books', 0)},
    ]

    context = {
        'page_obj': page_obj,
        'query': query,
        'selected_category': category_filter,
        'categories': categories,
        'total_products': len(all_products),
    }
    return render(request, 'store/home.html', context)


def product_detail(request, product_id):
    product = get_product_from_cache_or_api(product_id)
    if not product:
        messages.error(request, 'Product not found')
        return redirect('home')

    related = [p for p in get_all_products() if p.get('category') == product.get('category') and p['id'] != product['id']][:4]

    return render(request, 'store/product_detail.html', {'product': product, 'related_products': related})


def get_or_create_local_product(product_id):
    """Resolve a catalog product to the local database for cart/order support."""
    try:
        return Product.objects.get(id=product_id)
    except (Product.DoesNotExist, ValueError, TypeError):
        external_product = get_product_from_cache_or_api(product_id)
        if not external_product:
            return None

        category_name = external_product.get('category') or 'general'
        category, _ = Category.objects.get_or_create(name=category_name)
        sku = f"external-{external_product['id']}"
        product, _ = Product.objects.get_or_create(
            sku=sku,
            defaults={
                'title': external_product['title'],
                'description': external_product.get('description', ''),
                'price': Decimal(str(external_product['price'])),
                'image': external_product.get('image'),
                'category': category,
                'stock_quantity': 0,
                'in_stock': True,
            },
        )
        return product


# Cart views: note URL name expected for cart page is 'cart' in redirects

def cart_view(request):
    """Display shopping cart page"""
    cart_data = get_cart_data(request)
    
    context = {
        'cart_items': cart_data['cart_items'],
        'total_quantity': cart_data['total_quantity'],
        'total_price': cart_data['total_price'],
        'shipping': cart_data['shipping'],
        'tax': cart_data['tax'],
        'grand_total': cart_data['grand_total'],
        'shipping_remaining': cart_data['shipping_remaining'],
    }
    return render(request, 'store/cart.html', context)


@require_POST
def add_to_cart(request, product_id):
    product = get_or_create_local_product(product_id)
    if not product:
        messages.error(request, 'Product not found')
        return redirect('home')

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1
    quantity = max(1, min(quantity, 99))

    # ---- SESSION CART ----
    cart = request.session.get('cart', {'items': {}})
    items = cart['items']
    items[str(product.id)] = items.get(str(product.id), 0) + quantity
    request.session['cart'] = cart
    request.session.modified = True

    messages.success(request, f"✅ {product.title} added to your cart.")
    return redirect('cart')


@require_POST
def remove_from_cart(request, product_id):
    """Remove item from cart (session + database)"""
    cart = ensure_cart_session(request)
    
    # ✅ Remove from session cart
    if str(product_id) in cart['items']:
        del cart['items'][str(product_id)]
        save_cart_session(request)
        messages.success(request, 'Item removed from cart')
    else:
        messages.error(request, 'Item not found in cart')

    return redirect('cart')


def increase_quantity(request, product_id):
    """Increase item quantity"""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        
        if 'items' in cart and str(product_id) in cart['items']:
            cart['items'][str(product_id)] += 1
            request.session.modified = True
            messages.success(request, 'Quantity increased')
        else:
            messages.error(request, 'Item not found in cart')
    
    return redirect('cart')

def decrease_quantity(request, product_id):
    """Decrease item quantity"""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        
        if 'items' in cart and str(product_id) in cart['items']:
            if cart['items'][str(product_id)] > 1:
                cart['items'][str(product_id)] -= 1
                request.session.modified = True
                messages.success(request, 'Quantity decreased')
            else:
                # Remove item if quantity becomes 0
                del cart['items'][str(product_id)]
                request.session.modified = True
                messages.success(request, 'Item removed from cart')
        else:
            messages.error(request, 'Item not found in cart')
    
    return redirect('cart')

def clear_cart(request):
    request.session['cart'] = {'items': {}}
    request.session.modified = True

    messages.info(request, "🧹 Your cart has been cleared.")
    return redirect('cart')


# Debug / test utilities (safe to remove in production)

def add_test_product(request):
    cart = ensure_cart_session(request)
    cart['1'] = {'quantity': 1}
    save_cart_session(request)
    messages.success(request, 'Test product added')
    return redirect('cart')


def clear_cart_session(request):
    cart = ensure_cart_session(request)
    cart.clear()
    save_cart_session(request)
    messages.info(request, 'Cart session cleared')
    return redirect('cart')


def debug_session(request):
    cart = ensure_cart_session(request)
    info = {
        'session_key': request.session.session_key,
        'cart_in_session': 'cart' in request.session,
        'cart_data': request.session.get('cart', {}),
        'session_modified': request.session.modified,
    }
    return JsonResponse(info)


# ------------------ Orders / Checkout ------------------

def checkout(request):
    """
    Build cart items, compute totals and render checkout page.
    Uses Decimal everywhere to avoid mixing float + Decimal.
    """
    # build cart items (session + db merged as you already do)
    cart = request.session.get('cart', {'items': {}})
    cart_items = []
    total_price = Decimal('0.00')
    total_quantity = 0

    # Session items
    for product_id, quantity in cart.get('items', {}).items():
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            continue

        # product.price is a Decimal (from DecimalField)
        price = product.discounted_price if product.discounted_price is not None else product.price
        # Ensure price is Decimal
        if not isinstance(price, Decimal):
            price = Decimal(str(price))

        quantity = int(quantity)
        subtotal = (price * quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        cart_items.append({
            'id': product.id,
            'title': product.title,
            'price': price,
            'quantity': quantity,
            'subtotal': subtotal,
            'image': product.local_image.url if product.local_image else (product.image or ''),
        })

        total_price += subtotal
        total_quantity += quantity

    # DB items (if you store Cart model items)
    if request.user.is_authenticated:
        db_cart_items = Cart.objects.filter(user=request.user)
    else:
        session_key = request.session.session_key or request.session.create()
        db_cart_items = Cart.objects.filter(session_key=session_key)

    for db_item in db_cart_items:
        product = db_item.product
        price = product.discounted_price if product.discounted_price is not None else product.price
        if not isinstance(price, Decimal):
            price = Decimal(str(price))

        quantity = int(db_item.quantity)
        subtotal = (price * quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        cart_items.append({
            'id': product.id,
            'title': product.title,
            'price': price,
            'quantity': quantity,
            'subtotal': subtotal,
            'image': product.local_image.url if product.local_image else (product.image or ''),
        })

        total_price += subtotal
        total_quantity += quantity

    # SHIPPING and TAX (using Decimal)
    FREE_SHIPPING_THRESHOLD = Decimal('50.00')
    SHIPPING_FEE = Decimal('5.00')

    shipping_cost = Decimal('0.00') if total_price >= FREE_SHIPPING_THRESHOLD else SHIPPING_FEE
    tax_rate = Decimal('0.05')  # 5%
    tax = (total_price * tax_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    grand_total = (total_price + shipping_cost + tax).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    total_savings = Decimal('0.00')  # compute if you track discounts
    shipping_remaining = (FREE_SHIPPING_THRESHOLD - total_price) if total_price < FREE_SHIPPING_THRESHOLD else Decimal('0.00')

    context = {
        'cart_items': cart_items,
        'total_price': total_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'total_quantity': total_quantity,
        'shipping': shipping_cost,
        'tax': tax,
        'grand_total': grand_total,
        'total_savings': total_savings,
        'shipping_remaining': shipping_remaining.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
    }

    if request.method == 'POST':
        return process_checkout(request, cart_items, grand_total)

    return render(request, 'store/checkout.html', context)

@transaction.atomic
def process_checkout(request, cart_items, grand_total):
    """
    Create an Order and corresponding OrderItems.
    Clears session & DB cart after successful checkout.
    """
    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect('cart')

    # Get shipping address (assuming user has one)
    shipping_address = None
    if request.user.is_authenticated:
        shipping_address = UserAddress.objects.filter(user=request.user).first()

    # Create new order
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        shipping_address=shipping_address,
        payment_method=request.POST.get('payment_method', 'cash_on_delivery'),
        total_amount=grand_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        total_price=grand_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        status='pending',
        is_paid=False,
        created_at=timezone.now(),
    )

    # Add items to OrderItem
    for item in cart_items:
        product = Product.objects.get(id=item['id'])
        OrderItem.objects.create(
            order=order,
            product=product,
            product_title=product.title,
            quantity=item['quantity'],
            price=item['price'],
        )

        # Optional: reduce stock quantity
        if product.stock_quantity > 0:
            product.stock_quantity -= item['quantity']
            product.save()

    # Clear session-based cart
    if 'cart' in request.session:
        del request.session['cart']
        request.session.modified = True

    # Clear database-based cart (if using Cart model)
    if request.user.is_authenticated:
        Cart.objects.filter(user=request.user).delete()
    else:
        Cart.objects.filter(session_key=request.session.session_key).delete()

    messages.success(request, f"Order #{order.id} placed successfully!")
    return redirect('order_success')


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_confirmation.html', {'order': order, 'order_items': order.items.all()})


@login_required
def order_tracking(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/order_tracking.html', {'orders': orders})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/order_history.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_detail.html', {'order': order, 'order_items': order.items.all()})


# ------------------ Auth / Address / Misc ------------------

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Logged out')
    return render(request, 'store/logout.html')


@login_required
def address_list(request):
    addresses = UserAddress.objects.filter(user=request.user)
    return render(request, 'store/address_list.html', {'addresses': addresses})


@login_required
def add_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if form.cleaned_data.get('is_default') or not UserAddress.objects.filter(user=request.user).exists():
                UserAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
                address.is_default = True
            address.save()
            messages.success(request, 'Address added')
            return redirect('address_list')
    else:
        form = AddressForm()
    return render(request, 'store/add_address.html', {'form': form})


@login_required
def edit_address(request, address_id):
    address = get_object_or_404(UserAddress, id=address_id, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            if form.cleaned_data.get('default'):
                UserAddress.objects.filter(user=request.user, default=True).exclude(id=address.id).update(default=False)
            form.save()
            messages.success(request, 'Address updated')
            return redirect('address_list')
    else:
        form = AddressForm(instance=address)
    return render(request, 'store/edit_address.html', {'form': form, 'address': address})


@login_required
def delete_address(request, address_id):
    address = get_object_or_404(UserAddress, id=address_id, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted')
        return redirect('address_list')
    return render(request, 'store/delete_address.html', {'address': address})


def subscribe_newsletter(request):
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            messages.success(request, 'Thank you for subscribing')
            return redirect('home')
    else:
        form = NewsletterForm()
    return render(request, 'store/newsletter.html', {'form': form})


def faq_view(request):
    return render(request, 'store/faq.html')


def shipping_view(request):
    return render(request, 'store/shipping.html')


def returns_view(request):
    return render(request, 'store/returns.html')


def privacy_view(request):
    return render(request, 'store/privacy.html')


def terms_view(request):
    return render(request, 'store/terms.html')


@login_required
def account_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'store/account.html', {'user': request.user, 'orders': orders})

def about(request):
    return render(request, 'store/about.html')

from django.shortcuts import render, get_object_or_404
from .models import Order

@login_required
def track_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/track_order_detail.html', {'order': order})

def track_order_by_number(request):
    if request.method == 'POST':
        order_number = request.POST.get('order_number', '').strip()
        order = Order.objects.filter(tracking_number=order_number).first()
        if not order and order_number.isdigit():
            order = Order.objects.filter(id=int(order_number)).first()
        if order:
            return render(request, 'store/track_order_result.html', {
                'message': f'Order #{order.id} is currently {order.get_status_display().lower()}.',
                'order': order,
            })
        return render(request, 'store/track_order_result.html', {
            'message': 'No order was found for that tracking number.'
        })
    
    return render(request, 'store/track_order.html')

@csrf_exempt  # (Remove later when you use CSRF tokens in JS)
@require_POST
def add_to_cart_api(request):
    """
    Adds a product to the cart and returns updated cart count
    """
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

    if request.user.is_authenticated:
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        cart_count = Cart.objects.filter(user=request.user).aggregate(total=Sum('quantity'))['total'] or 0
    else:
        session_key = request.session.session_key or request.session.create()
        cart_item, created = Cart.objects.get_or_create(
            session_key=request.session.session_key,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        cart_count = Cart.objects.filter(session_key=request.session.session_key).aggregate(total=Sum('quantity'))['total'] or 0

    return JsonResponse({'message': 'Added to cart successfully', 'cart_count': cart_count})

def cart_count_api(request):
    cart = request.session.get('cart', {'items': {}})
    cart_count = sum(
        max(0, int(quantity))
        for quantity in cart.get('items', {}).values()
        if str(quantity).lstrip('-').isdigit()
    )

    return JsonResponse({'cart_count': cart_count})

def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

def cart(request):
    cart = ensure_cart_session(request)
    cart_items = []
    total_amount = Decimal('0.00')
    total_quantity = 0

    # ---- SESSION CART ----
    for product_id, quantity in cart['items'].items():
        try:
            product = get_or_create_local_product(product_id)
            if not product:
                continue
            quantity = max(1, int(quantity))
            price = product.get_final_price()
            subtotal = price * quantity

            cart_items.append({
                'id': product.id,
                'name': product.title,
                'price': price,
                'quantity': quantity,
                'subtotal': subtotal,
                'image': product.image or (product.local_image.url if getattr(product, 'local_image', None) else ''),
                'stock': getattr(product, 'stock_quantity', 0),
            })
            total_amount += subtotal
            total_quantity += quantity
        except (Product.DoesNotExist, ValueError, TypeError):
            continue

    # ---- COMPUTE TOTALS ----
    shipping = Decimal('0.00') if total_amount >= 50 else Decimal('5.00')
    tax = total_amount * Decimal('0.05')
    grand_total = total_amount + shipping + tax
    shipping_remaining = max(Decimal('0.00'), Decimal('50.00') - total_amount)

    context = {
        'cart_items': cart_items,
        'total_quantity': total_quantity,
        'shipping': shipping,
        'tax': tax,
        'grand_total': grand_total,
        'shipping_remaining': shipping_remaining,
        'total_amount': total_amount,
    }

    return render(request, 'store/cart.html', context)



def get_product_by_id(product_id):
    """Get product from your actual Product model"""
    try:
        # Return the actual Product object
        return Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return None

@login_required
def checkout(request):
    cart = ensure_cart_session(request)
    cart_items = []
    total_price = Decimal('0.00')
    total_quantity = 0

    # ---- Loop through session cart ----
    for product_id, quantity in cart['items'].items():
        try:
            product = get_or_create_local_product(product_id)
            if not product:
                continue
            quantity = max(1, int(quantity))
            subtotal = product.get_final_price() * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal,
            })
            total_price += subtotal
            total_quantity += quantity
        except (Product.DoesNotExist, ValueError, TypeError):
            continue

    # ---- Shipping & total ----
    order_shipping_cost = Decimal('0.00') if total_price > 50 else Decimal('5.00')
    total_amount = total_price + order_shipping_cost

    # ---- Save Order ----
    if request.method == 'POST':
        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            total_amount=total_amount,
            order_shipping_cost=order_shipping_cost,
            status='pending',
            payment_method=request.POST.get('payment_method', 'cash_on_delivery'),
        )

        # Save Order Items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['product'].price
            )

        # Clear cart
        request.session['cart'] = {'items': {}}
        request.session.modified = True

        return render(request, 'store/order_success.html', {'order': order})

    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'order_shipping_cost': order_shipping_cost,
        'total_amount': total_amount,
        'total_quantity': total_quantity,
    })


    
def get_product_by_id(product_id):
    try:
        return Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return None


def order_success(request):
    return render(request, 'store/order_success.html')

def create_order(request, cart_items, shipping_address, payment_method, total_amount):
    # Implement your order creation logic here
    # This is a placeholder - you'll need to create an Order model
    from .models import Order, OrderItem
    
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        total_amount=total_amount,
        payment_method=payment_method,
        shipping_address=shipping_address,
        # ... other order fields
    )
    
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item['product'],
            quantity=item['quantity'],
            price=item['product'].price
        )
    
    return order

@require_POST
def update_quantity(request, product_id, action):
    """Update item quantity (increase/decrease) in both session & database"""
    cart = ensure_cart_session(request)
    product_id_str = str(product_id)
    
    # ✅ Check if product exists in session cart
    if product_id_str not in cart['items']:
        messages.error(request, 'Item not found in cart')
        return redirect('cart')
    
    # ✅ Handle quantity update in session
    if action == 'increase':
        cart['items'][product_id_str] += 1
        messages.success(request, 'Quantity increased')
    elif action == 'decrease':
        if cart['items'][product_id_str] > 1:
            cart['items'][product_id_str] -= 1
            messages.success(request, 'Quantity decreased')
        else:
            del cart['items'][product_id_str]
            messages.success(request, 'Item removed from cart')
    
    save_cart_session(request)

    # ✅ Handle quantity update in database cart
    session_key = request.session.session_key or request.session.create()
    user = request.user if request.user.is_authenticated else None

    try:
        cart_item = Cart.objects.get(
            product_id=product_id,
            user=user,
            session_key=session_key
        )
        if action == 'increase':
            cart_item.quantity += 1
            cart_item.save()
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
    except Cart.DoesNotExist:
        pass  # Safe to ignore if item isn't in DB
    
    return redirect('cart')

@require_POST
def clear_cart(request):
    """Clear entire cart"""
    cart = ensure_cart_session(request)
    cart['items'] = {}
    save_cart_session(request)
    messages.success(request, 'Cart cleared successfully')
    return redirect('cart')


def debug_track(request):
    tracking_id = request.GET.get('tracking_id', '').strip()
    
    print(f"=== DEBUG TRACK VIEW ===")
    print(f"Tracking ID: '{tracking_id}'")
    
    if tracking_id:
        try:
            tracking = OrderTracking.objects.get(tracking_id=tracking_id)
            print(f"✅ FOUND: {tracking.tracking_id} - {tracking.status}")
            
            # Simple direct response
            from django.http import HttpResponse
            return HttpResponse(f"""
            <h1>DEBUG WORKED!</h1>
            <p>Tracking ID: {tracking.tracking_id}</p>
            <p>Status: {tracking.status}</p>
            <p><a href="/track-order/">Back to main</a></p>
            """)
            
        except OrderTracking.DoesNotExist:
            print(f"❌ NOT FOUND: {tracking_id}")
            from django.http import HttpResponse
            return HttpResponse(f"NOT FOUND: {tracking_id}")
    
    return HttpResponse("Please add ?tracking_id=TEST001 to URL")

def debug_urls(request):
    """Temporary view to debug URL routing"""
    print("🎯 DEBUG URLS VIEW IS WORKING!")
    print("🔍 This proves URLs are configured correctly")
    
    from django.urls import get_resolver
    url_patterns = []
    
    # Get all registered URLs
    resolver = get_resolver()
    for pattern in resolver.url_patterns:
        url_patterns.append(str(pattern))
    
    return HttpResponse(f"<h1>URL Debug</h1><p>This view works!</p><p>Registered patterns: {url_patterns}</p>")

def simple_test(request):
    print("🎯 SIMPLE TEST VIEW IS WORKING!")
    return HttpResponse("SIMPLE TEST WORKS!")