from django.urls import path
from . import views


urlpatterns = [
    # Basic pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    
    # Product pages
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    
    # Cart URLs
    path('cart/', views.cart, name='cart'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/increase/<int:product_id>/', views.increase_quantity, name='increase_quantity'),
    path('cart/decrease/<int:product_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
    
    # Order URLs
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/', views.order_success, name='order_success'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('order-detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order-tracking/', views.order_tracking, name='order_tracking'),
    path('order-history/', views.order_history, name='order_history'),
    path('track-order/<int:order_id>/', views.track_order_detail, name='track_order_detail'),
    path('track-order/', views.track_order_by_number, name='track_order_by_number'),
    # Address URLs
    path('addresses/', views.address_list, name='address_list'),
    path('addresses/add/', views.add_address, name='add_address'),
    path('addresses/edit/<int:address_id>/', views.edit_address, name='edit_address'),
    path('addresses/delete/<int:address_id>/', views.delete_address, name='delete_address'),
    
    # Other
    path('newsletter/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('api/cart-count/', views.cart_count_api, name='cart_count_api'),
    path('api/cart_count/', views.cart_count_api, name='cart_count_api'),
    path('faq/', views.faq_view, name='faq'),
    path('shipping-info/', views.shipping_view, name='shipping'),
    path('returns-policy/', views.returns_view, name='returns'),
    path('privacy-policy/', views.privacy_view, name='privacy'),
    path('terms-of-service/', views.terms_view, name='terms'),
    path('my-account/', views.account_view, name='account'),
    path('api/add-to-cart/', views.add_to_cart_api, name='add_to_cart_api'),
    path('cart/update/<int:product_id>/<str:action>/', views.update_quantity, name='update_quantity'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),

]