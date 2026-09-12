from django.contrib import admin
from .models import Product, Category, Cart, UserAddress, Order, OrderItem, ProductReview, Wishlist

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'image', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'title', 
        'category', 
        'price', 
        'discounted_price', 
        'in_stock', 
        'stock_quantity',
        'created_at'
    ]
    list_filter = ['category', 'in_stock', 'created_at']
    search_fields = ['title', 'description', 'sku']
    list_editable = ['price', 'discounted_price', 'in_stock', 'stock_quantity']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category')
        }),
        ('Pricing', {
            'fields': ('price', 'discounted_price')
        }),
        ('Images', {
            'fields': ('image', 'local_image')
        }),
        ('Inventory', {
            'fields': ('in_stock', 'stock_quantity', 'sku')
        }),
        ('Product Details', {
            'fields': ('weight', 'dimensions')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity', 'session_key', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__title', 'session_key']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'full_name', 
        'city', 
        'state', 
        'postal_code', 
        'is_default', 
        'created_at'
    ]
    list_filter = ['city', 'state', 'country', 'is_default', 'created_at']
    search_fields = ['user__username', 'full_name', 'city', 'state']
    readonly_fields = ['created_at', 'updated_at']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['get_total_price']
    
    def get_total_price(self, obj):
        return f"${obj.get_total_price()}"
    get_total_price.short_description = 'Total Price'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'user', 
        'total_price', 
        'status', 
        'payment_method', 
        'payment_status', 
        'created_at'
    ]
    list_filter = ['status', 'payment_method', 'payment_status', 'created_at']
    search_fields = ['user__username', 'tracking_number', 'id']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'shipping_address', 'total_price', 'status')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'payment_status', 'payment_id')
        }),
        ('Delivery Information', {
            'fields': (
                'tracking_number', 
                'carrier', 
                'estimated_delivery', 
                'shipped_at', 
                'delivered_at'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'order', 
        'product_title', 
        'quantity', 
        'price', 
        'get_total_price'
    ]
    list_filter = ['order__status']
    search_fields = ['product_title', 'order__id']
    
    def get_total_price(self, obj):
        return f"${obj.get_total_price()}"
    get_total_price.short_description = 'Total Price'

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = [
        'product', 
        'user', 
        'rating', 
        'title', 
        'is_approved', 
        'created_at'
    ]
    list_filter = ['rating', 'is_approved', 'created_at']
    search_fields = ['product__title', 'user__username', 'title']
    list_editable = ['is_approved']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__title']
    readonly_fields = ['created_at']

# Customize admin site
admin.site.site_header = "MyAmazon Administration"
admin.site.site_title = "MyAmazon Admin Portal"
admin.site.index_title = "Welcome to MyAmazon Admin Portal"