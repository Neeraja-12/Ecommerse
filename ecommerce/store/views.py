# store/views.py
from decimal import Decimal, ROUND_HALF_UP
import random
import string
from collections import Counter

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import (
    Category, Product, Cart, UserAddress,
    Order, OrderItem, ProductReview, Wishlist, RecentlyViewed,
    OrderTracking,
)
from .forms import (
    CustomUserCreationForm, AddressForm,
    CheckoutForm, NewsletterForm,
)


# ============================================================
# HELPERS
# ============================================================

def generate_tracking_number():
    letters = ''.join(random.choices(string.ascii_uppercase, k=4))
    numbers = ''.join(random.choices(string.digits, k=8))
    return f"TRK{letters}{numbers}"


def product_to_dict(p):
    """Convert a Product model instance to a plain dict for templates."""
    return {
        'id': p.id,
        'title': p.title,
        'price': float(p.discounted_price or p.price),
        'original_price': float(p.price),
        'category': p.category.name if p.category else 'general',
        'description': p.description or '',
        'image': p.image or (p.local_image.url if p.local_image else ''),
        'in_stock': p.in_stock,
        'stock_quantity': p.stock_quantity,
    }


def get_all_products():
    """Return all in-stock products from the DB as dicts."""
    products = Product.objects.filter(in_stock=True).select_related('category')
    return [product_to_dict(p) for p in products]


def get_product_from_cache_or_api(product_id):
    """Kept for backwards compatibility — now reads from DB."""
    try:
        p = Product.objects.select_related('category').get(id=product_id)
        return product_to_dict(p)
    except Product.DoesNotExist:
        return None


def get_or_create_local_product(product_id):
    """Resolve a product ID to a local Product instance."""
    try:
        return Product.objects.get(id=product_id)
    except (Product.DoesNotExist, ValueError, TypeError):
        return None


# ============================================================
# SESSION CART HELPERS
# ============================================================

def ensure_cart_session(request):
    """Guarantee request.session['cart'] = {'items': {}} exists."""
    if not request.session.session_key:
        request.session.create()
    if 'cart' not in request.session or 'items' not in request.session.get('cart', {}):
        request.session['cart'] = {'items': {}}
        request.session.modified = True
    return request.session['cart']


def save_cart_session(request):
    request.session.modified = True
    request.session.save()


def get_cart_data(request):
    """Return cart items (expanded with product info) + all totals."""
    cart = ensure_cart_session(request)
    cart_items = []
    failed = []

    for product_id, quantity in list(cart['items'].items()):
        product = get_or_create_local_product(product_id)
        if not product:
            failed.append(product_id)
            continue

        try:
            quantity = max(1, int(quantity))
        except (TypeError, ValueError):
            quantity = 1

        unit_price = product.discounted_price or product.price
        unit_price = Decimal(str(unit_price))
        subtotal = (unit_price * quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        cart_items.append({
            'id': product.id,
            'title': product.title,
            'price': unit_price,
            'quantity': quantity,
            'subtotal': subtotal,
            'image': product.image or (product.local_image.url if product.local_image else ''),
            'category': product.category.name if product.category else 'general',
            'stock': product.stock_quantity,
        })

    if failed:
        for pid in failed:
            cart['items'].pop(str(pid), None)
        save_cart_session(request)

    subtotal_total = sum(item['subtotal'] for item in cart_items)
    shipping = Decimal('0.00') if subtotal_total >= 50 else Decimal('5.00')
    tax = (subtotal_total * Decimal('0.05')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    grand_total = (subtotal_total + shipping + tax).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    total_quantity = sum(item['quantity'] for item in cart_items)
    shipping_remaining = max(Decimal('0.00'), Decimal('50.00') - subtotal_total)

    return {
        'cart_items': cart_items,
        'total_quantity': total_quantity,
        'total_price': subtotal_total,
        'shipping': shipping,
        'tax': tax,
        'grand_total': grand_total,
        'shipping_remaining': shipping_remaining,
    }


# ============================================================
# HOME + PRODUCTS
# ============================================================

def home(request):
    query = request.GET.get('q', '').strip()
    category_filter = request.GET.get('category', '').strip()

    all_products = get_all_products()

    if query:
        all_products = [p for p in all_products if query.lower() in p['title'].lower()]
    if category_filter:
        all_products = [p for p in all_products if p['category'].lower() == category_filter.lower()]

    paginator = Paginator(all_products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    counter = Counter(p['category'] for p in all_products)
    categories = [
        {'name': 'Electronics', 'slug': 'electronics', 'count': counter.get('electronics', 0) + counter.get('Electronics', 0)},
        {'name': 'Fashion', 'slug': 'fashion', 'count': counter.get('fashion', 0) + counter.get('Fashion', 0) + counter.get('jewelery', 0)},
        {'name': 'Home', 'slug': 'home', 'count': counter.get('home', 0) + counter.get('Home', 0)},
        {'name': 'Books', 'slug': 'books', 'count': counter.get('books', 0) + counter.get('Books', 0)},
    ]

    return render(request, 'store/home.html', {
        'page_obj': page_obj,
        'query': query,
        'selected_category': category_filter,
        'categories': categories,
        'total_products': len(all_products),
    })


def product_detail(request, product_id):
    db_product = Product.objects.filter(id=product_id).select_related('category').first()
    if not db_product:
        messages.error(request, 'Product not found')
        return redirect('home')

    # Related products — same category
    related = []
    if db_product.category:
        related_qs = Product.objects.filter(
            category=db_product.category, in_stock=True
        ).exclude(id=db_product.id)[:4]
        related = [product_to_dict(p) for p in related_qs]

    # Recently viewed — update + fetch
    recently = []
    if request.user.is_authenticated:
        RecentlyViewed.objects.update_or_create(
            user=request.user, product=db_product
        )
        recent_qs = RecentlyViewed.objects.filter(
            user=request.user
        ).exclude(product=db_product).select_related('product', 'product__category')[:4]
        recently = [product_to_dict(r.product) for r in recent_qs]

    # Reviews (approved only)
    reviews = ProductReview.objects.filter(
        product=db_product, is_approved=True
    ).order_by('-created_at')

    # Was this product wishlisted by the user?
    is_wishlisted = (
        request.user.is_authenticated and
        Wishlist.objects.filter(user=request.user, product=db_product).exists()
    )

    return render(request, 'store/product_detail.html', {
        'product': product_to_dict(db_product),
        'related_products': related,
        'recently_viewed': recently,
        'reviews': reviews,
        'is_wishlisted': is_wishlisted,
    })


# ============================================================
# CART
# ============================================================

def cart(request):
    """Display the shopping cart."""
    cart_data = get_cart_data(request)
    return render(request, 'store/cart.html', cart_data)


# Keep alias for older URLs
cart_view = cart


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

    cart = ensure_cart_session(request)
    pid = str(product.id)
    cart['items'][pid] = cart['items'].get(pid, 0) + quantity
    save_cart_session(request)

    messages.success(request, f"✅ {product.title} added to your cart.")
    return redirect('cart')


@require_POST
def remove_from_cart(request, product_id):
    cart = ensure_cart_session(request)
    pid = str(product_id)
    if pid in cart['items']:
        del cart['items'][pid]
        save_cart_session(request)
        messages.success(request, 'Item removed from cart')
    else:
        messages.error(request, 'Item not found in cart')
    return redirect('cart')


@require_POST
def update_quantity(request, product_id, action):
    """Increase / decrease quantity in one view."""
    cart = ensure_cart_session(request)
    pid = str(product_id)

    if pid not in cart['items']:
        messages.error(request, 'Item not found in cart')
        return redirect('cart')

    if action == 'increase':
        cart['items'][pid] += 1
        messages.success(request, 'Quantity increased')
    elif action == 'decrease':
        if cart['items'][pid] > 1:
            cart['items'][pid] -= 1
            messages.success(request, 'Quantity decreased')
        else:
            del cart['items'][pid]
            messages.success(request, 'Item removed from cart')

    save_cart_session(request)
    return redirect('cart')


@require_POST
def increase_quantity(request, product_id):
    return update_quantity(request, product_id, 'increase')


@require_POST
def decrease_quantity(request, product_id):
    return update_quantity(request, product_id, 'decrease')


@require_POST
def clear_cart(request):
    cart = ensure_cart_session(request)
    cart['items'] = {}
    save_cart_session(request)
    messages.success(request, 'Cart cleared successfully')
    return redirect('cart')


def cart_count_api(request):
    cart_data = request.session.get('cart', {'items': {}})
    count = sum(
        max(0, int(q))
        for q in cart_data.get('items', {}).values()
        if str(q).lstrip('-').isdigit()
    )
    return JsonResponse({'cart_count': count})


# ============================================================
# WISHLIST
# ============================================================

@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(
        user=request.user
    ).select_related('product', 'product__category')
    return render(request, 'store/wishlist.html', {
        'items': [{'product': product_to_dict(i.product), 'added': i.created_at} for i in items],
    })


@login_required
@require_POST
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        obj.delete()
        return JsonResponse({'status': 'removed', 'in_wishlist': False})
    return JsonResponse({'status': 'added', 'in_wishlist': True})


# ============================================================
# REVIEWS
# ============================================================

@login_required
@require_POST
def submit_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    rating = request.POST.get('rating')
    title = request.POST.get('title', '').strip()
    comment = request.POST.get('comment', '').strip()

    if not rating or not comment:
        return JsonResponse({'error': 'Rating and comment are required'}, status=400)

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Rating must be 1–5'}, status=400)

    ProductReview.objects.update_or_create(
        product=product, user=request.user,
        defaults={
            'rating': rating,
            'title': title,
            'comment': comment,
            'is_approved': True,
        }
    )
    return JsonResponse({'status': 'ok'})


# ============================================================
# CHECKOUT + ORDERS
# ============================================================

@login_required
def checkout(request):
    cart_data = get_cart_data(request)
    if not cart_data['cart_items']:
        messages.warning(request, 'Your cart is empty')
        return redirect('cart')

    addresses = UserAddress.objects.filter(user=request.user)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        address_form = AddressForm(request.POST)
        selected_address_id = request.POST.get('selected_address')

        if not form.is_valid():
            messages.error(request, 'Please correct the errors below')
            return render(request, 'store/checkout.html', {
                'form': form, 'address_form': address_form,
                'addresses': addresses, **cart_data,
            })

        shipping_address = None
        if selected_address_id == 'new':
            if not address_form.is_valid():
                messages.error(request, 'Please fix the address form')
                return render(request, 'store/checkout.html', {
                    'form': form, 'address_form': address_form,
                    'addresses': addresses, **cart_data,
                })
            addr = address_form.save(commit=False)
            addr.user = request.user
            if address_form.cleaned_data.get('is_default'):
                UserAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
                addr.is_default = True
            addr.save()
            shipping_address = addr
        elif selected_address_id:
            shipping_address = get_object_or_404(
                UserAddress, id=selected_address_id, user=request.user
            )
        else:
            messages.error(request, 'Please select or add a shipping address')
            return render(request, 'store/checkout.html', {
                'form': form, 'address_form': address_form,
                'addresses': addresses, **cart_data,
            })

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    shipping_address=shipping_address,
                    payment_method=form.cleaned_data.get('payment_method', 'cash_on_delivery'),
                    total_price=cart_data['grand_total'],
                    
                    status='pending',
                    tracking_number=generate_tracking_number(),
                    estimated_delivery=(timezone.now() + timezone.timedelta(days=7)).date(),
                )

                for item in cart_data['cart_items']:
                    OrderItem.objects.create(
                        order=order,
                        product_id=item['id'],
                        product_title=item['title'],
                        quantity=item['quantity'],
                        price=item['price'],
                    )
                    # Decrement stock
                    p = Product.objects.get(id=item['id'])
                    if p.stock_quantity > 0:
                        p.stock_quantity = max(0, p.stock_quantity - item['quantity'])
                        p.save()

                # Clear cart
                cart_obj = ensure_cart_session(request)
                cart_obj['items'] = {}
                save_cart_session(request)

            messages.success(request, f'Order #{order.id} placed successfully')
            return redirect('order_confirmation', order_id=order.id)

        except Exception as e:
            messages.error(request, f'Error placing order: {e}')

    else:
        form = CheckoutForm()
        address_form = AddressForm()

    return render(request, 'store/checkout.html', {
        'form': form,
        'address_form': address_form,
        'addresses': addresses,
        **cart_data,
    })


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_confirmation.html', {
        'order': order, 'order_items': order.items.all(),
    })


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
    return render(request, 'store/order_detail.html', {
        'order': order, 'order_items': order.items.all(),
    })


def order_success(request):
    return render(request, 'store/order_success.html')


@login_required
def track_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/track_order_detail.html', {'order': order})


def track_order(request):
    if request.method == 'POST':
        raw = request.POST.get('order_number', '').strip()
        cleaned = raw.lstrip('#').strip()

        order = None
        # Try as tracking number first
        if raw:
            order = Order.objects.filter(tracking_number=raw).first()

        # Try as order ID (numeric)
        if not order and cleaned.isdigit():
            order = Order.objects.filter(id=int(cleaned)).first()

        return render(request, 'store/track_order_result.html', {
            'searched': raw,
            'order': order,
        })
    return render(request, 'store/track_order.html')


# ============================================================
# AUTH
# ============================================================

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


def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def account_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'store/account.html', {
        'user': request.user, 'orders': orders,
    })


# ============================================================
# ADDRESSES
# ============================================================

@login_required
def address_list(request):
    addresses = UserAddress.objects.filter(user=request.user)
    return render(request, 'store/address_list.html', {'addresses': addresses})


@login_required
def add_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            addr = form.save(commit=False)
            addr.user = request.user
            if form.cleaned_data.get('is_default') or not UserAddress.objects.filter(user=request.user).exists():
                UserAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
                addr.is_default = True
            addr.save()
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
            if form.cleaned_data.get('is_default'):
                UserAddress.objects.filter(user=request.user, is_default=True).exclude(id=address.id).update(is_default=False)
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


# ============================================================
# STATIC / INFO PAGES
# ============================================================

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


def about(request):
    return render(request, 'store/about.html')


# ============================================================
# JSON API ENDPOINTS (kept for compatibility)
# ============================================================

@csrf_exempt
@require_POST
def add_to_cart_api(request):
    """AJAX endpoint — adds to session cart, returns new count."""
    product_id = request.POST.get('product_id')
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1
    quantity = max(1, min(quantity, 99))

    product = get_or_create_local_product(product_id)
    if not product:
        return JsonResponse({'error': 'Product not found'}, status=404)

    cart = ensure_cart_session(request)
    pid = str(product.id)
    cart['items'][pid] = cart['items'].get(pid, 0) + quantity
    save_cart_session(request)

    count = sum(
        max(0, int(q)) for q in cart['items'].values()
        if str(q).lstrip('-').isdigit()
    )
    return JsonResponse({
        'message': 'Added to cart successfully',
        'cart_count': count,
    })


# ============================================================
# DEBUG (safe to delete in production)
# ============================================================

def debug_session(request):
    cart = ensure_cart_session(request)
    return JsonResponse({
        'session_key': request.session.session_key,
        'cart_in_session': 'cart' in request.session,
        'cart_data': request.session.get('cart', {}),
        'session_modified': request.session.modified,
    })


def simple_test(request):
    return HttpResponse("SIMPLE TEST WORKS!")