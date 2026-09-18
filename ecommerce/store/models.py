# store/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator


# ============================================================
# CATEGORY
# ============================================================

class Category(models.Model):
    """Main category model for products."""
    name = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


# ============================================================
# PRODUCT
# ============================================================

class Product(models.Model):
    """Main product model."""
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    discounted_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01)]
    )
    image = models.URLField(blank=True, null=True)
    local_image = models.ImageField(upload_to='products/', blank=True, null=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='products'
    )
    in_stock = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Product metadata
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    weight = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    dimensions = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['category']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_on_sale(self):
        return self.discounted_price is not None and self.discounted_price < self.price

    @property
    def discount_percentage(self):
        if self.is_on_sale:
            return int(((self.price - self.discounted_price) / self.price) * 100)
        return 0

    def get_final_price(self):
        return self.discounted_price if self.is_on_sale else self.price

    @property
    def average_rating(self):
        agg = self.reviews.filter(is_approved=True).aggregate(avg=models.Avg('rating'))
        return round(agg['avg'] or 0, 1)

    @property
    def review_count(self):
        return self.reviews.filter(is_approved=True).count()


# ============================================================
# CART (database-backed; session cart is the active one)
# ============================================================

class Cart(models.Model):
    """Shopping cart supporting authenticated users and sessions."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Cart Items"
        unique_together = [['user', 'product'], ['session_key', 'product']]

    def get_total_price(self):
        return self.quantity * self.product.get_final_price()

    def __str__(self):
        return f"{self.product.title} x {self.quantity}"


# ============================================================
# USER ADDRESS
# ============================================================

class UserAddress(models.Model):
    """User shipping address."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=100)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=50, default='United States')
    phone_number = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Address"
        verbose_name_plural = "User Addresses"
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.address_line1}, {self.city}"

    def get_full_address(self):
        parts = [
            self.address_line1,
            self.address_line2,
            f"{self.city}, {self.state} {self.postal_code}",
            self.country,
        ]
        return ', '.join(p for p in parts if p)


# ============================================================
# ORDER + ORDER ITEM
# ============================================================

class Order(models.Model):
    """Order model with tracking."""
    PAYMENT_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('paypal', 'PayPal'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('digital_wallet', 'Digital Wallet'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    shipping_address = models.ForeignKey(UserAddress, on_delete=models.SET_NULL, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='credit_card')
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_paid = models.BooleanField(default=False)

    # Payment
    payment_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('paid', 'Paid'),
                 ('failed', 'Failed'), ('refunded', 'Refunded')],
        default='pending'
    )
    payment_id = models.CharField(max_length=100, blank=True, null=True)

    # Delivery tracking
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    estimated_delivery = models.DateField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    carrier = models.CharField(
        max_length=100, blank=True, null=True, default='MyAmazon Logistics'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['tracking_number']),
        ]

    def __str__(self):
        return f"Order #{self.id} - {self.user.username} - {self.status}"

    def get_status_percentage(self):
        weights = {
            'pending': 0, 'confirmed': 20, 'processing': 40,
            'shipped': 60, 'out_for_delivery': 80, 'delivered': 100,
            'cancelled': 0, 'refunded': 0,
        }
        return weights.get(self.status, 0)

    def get_status_timeline(self):
        timeline = [{
            'status': 'pending',
            'label': 'Order Placed',
            'time': self.created_at,
            'completed': self.status != 'pending',
        }]

        status_flow = [
            ('confirmed', 'Order Confirmed'),
            ('processing', 'Processing'),
            ('shipped', 'Shipped'),
            ('out_for_delivery', 'Out for Delivery'),
            ('delivered', 'Delivered'),
        ]

        current_index = -1
        for i, (status, _) in enumerate(status_flow):
            if status == self.status:
                current_index = i
                break

        for i, (status, label) in enumerate(status_flow):
            if i <= current_index:
                timeline.append({
                    'status': status,
                    'label': label,
                    'time': self.updated_at,
                    'completed': True,
                })

        return timeline

    def save(self, *args, **kwargs):
        if self.status == 'shipped' and not self.shipped_at:
            self.shipped_at = timezone.now()
        elif self.status == 'delivered' and not self.delivered_at:
            self.delivered_at = timezone.now()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """Individual line items in an order."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, related_name='order_items'
    )
    product_title = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def get_total_price(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.product_title} x {self.quantity} - ${self.get_total_price()}"


# ============================================================
# PRODUCT REVIEW
# ============================================================

class ProductReview(models.Model):
    """Product reviews."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Product Review"
        verbose_name_plural = "Product Reviews"
        unique_together = ['product', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"Review for {self.product.title} by {self.user.username}"


# ============================================================
# WISHLIST
# ============================================================

class Wishlist(models.Model):
    """User wishlist."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Wishlist"
        verbose_name_plural = "Wishlist Items"
        unique_together = ['user', 'product']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} → {self.product.title}"


# ============================================================
# RECENTLY VIEWED
# ============================================================

class RecentlyViewed(models.Model):
    """Track products a user recently viewed."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recently_viewed')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Recently Viewed"
        verbose_name_plural = "Recently Viewed"
        unique_together = ('user', 'product')
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.user.username} viewed {self.product.title}"


# ============================================================
# ORDER TRACKING
# ============================================================

class OrderTracking(models.Model):
    """Optional tracking record keyed by tracking_id."""
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name='tracking',
        null=True, blank=True
    )
    tracking_id = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=50, default='Pending')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order Tracking"
        verbose_name_plural = "Order Trackings"

    def __str__(self):
        return f"{self.tracking_id} — {self.status}"