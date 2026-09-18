from django.urls import path
from . import views


urlpatterns = [
    # ============================================================
    # BASIC PAGES
    # ============================================================
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),

    # ============================================================
    # PRODUCTS
    # ============================================================
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    # ============================================================
    # CART
    # ============================================================
    path('cart/', views.cart, name='cart'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/increase/<int:product_id>/', views.increase_quantity, name='increase_quantity'),
    path('cart/decrease/<int:product_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('cart/update/<int:product_id>/<str:action>/', views.update_quantity, name='update_quantity'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),

    # ============================================================
    # WISHLIST
    # ============================================================
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),

    # ============================================================
    # REVIEWS
    # ============================================================
    path('review/<int:product_id>/', views.submit_review, name='submit_review'),

    # ============================================================
    # CHECKOUT / ORDERS
    # ============================================================
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/', views.order_success, name='order_success'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('order-detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order-history/', views.order_history, name='order_history'),
    path('order-tracking/', views.order_tracking, name='order_tracking'),

    # Tracking (named 'track_order' so templates work)
    path('track-order/', views.track_order, name='track_order'),
    path('track-order/<int:order_id>/', views.track_order_detail, name='track_order_detail'),

    # ============================================================
    # ADDRESSES
    # ============================================================
    path('addresses/', views.address_list, name='address_list'),
    path('addresses/add/', views.add_address, name='add_address'),
    path('addresses/edit/<int:address_id>/', views.edit_address, name='edit_address'),
    path('addresses/delete/<int:address_id>/', views.delete_address, name='delete_address'),

    # ============================================================
    # AUTH / ACCOUNT
    # ============================================================
    path('signup/', views.signup, name='signup'),
    path('logout/', views.custom_logout, name='logout'),
    path('my-account/', views.account_view, name='account'),

    # ============================================================
    # INFO PAGES
    # ============================================================
    path('newsletter/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('faq/', views.faq_view, name='faq'),
    path('shipping-info/', views.shipping_view, name='shipping'),
    path('returns-policy/', views.returns_view, name='returns'),
    path('privacy-policy/', views.privacy_view, name='privacy'),
    path('terms-of-service/', views.terms_view, name='terms'),

    # ============================================================
    # JSON APIs (AJAX endpoints)
    # ============================================================
    path('api/cart-count/', views.cart_count_api, name='cart_count_api'),
    path('api/add-to-cart/', views.add_to_cart_api, name='add_to_cart_api'),
]