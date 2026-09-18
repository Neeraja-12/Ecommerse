import time
from django.utils.deprecation import MiddlewareMixin
import threading

class EnsureSessionMiddleware(MiddlewareMixin):
    """
    Middleware to ensure session exists for all requests
    """
    
    def process_request(self, request):
        """Called before processing the request"""
        
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
            print("🔄 SESSION DEBUG: Created new session")
        
        # Debug session state for specific paths
        if self._should_debug(request):
            self._log_session_state(request, "BEFORE")
    
    def process_response(self, request, response):
        """Called after processing the request"""
        
        # Debug session state after request processing
        if self._should_debug(request):
            self._log_session_state(request, "AFTER")
            print(f"📦 RESPONSE DEBUG: Status {response.status_code}")
        
        return response
    
    def _should_debug(self, request):
        """Determine if we should debug this request"""
        debug_paths = [
            '/cart/', '/add-to-cart/', '/checkout/', 
            '/product/', '/manual-add/', '/test-cart-flow/',
            '/session-test/', '/debug-cart/'
        ]
        return any(path in request.path for path in debug_paths)
    
    def _log_session_state(self, request, stage):
        """Log detailed session state"""
        cart = request.session.get('cart', {})
        session_keys = list(request.session.keys())
        
        print(f"\n{'='*50}")
        print(f"🎯 {stage} REQUEST: {request.method} {request.path}")
        print(f"🔑 Session Key: {request.session.session_key}")
        print(f"📝 Session Modified: {request.session.modified}")
        print(f"🗂️  Session Keys: {session_keys}")
        print(f"🛒 Cart Contents: {cart}")
        print(f"📊 Cart Items Count: {len(cart)}")
        
        # Detailed cart analysis
        if cart:
            total_quantity = 0
            for product_id, item_data in cart.items():
                if isinstance(item_data, dict):
                    quantity = item_data.get('quantity', 0)
                else:
                    quantity = int(item_data) if str(item_data).isdigit() else 0
                total_quantity += quantity
                print(f"   📦 Product {product_id}: {quantity} units")
            
            print(f"   📈 Total Quantity: {total_quantity}")
        print(f"{'='*50}\n")


class CartDebugMiddleware(MiddlewareMixin):
    """
    Advanced cart debugging middleware with performance tracking
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_count = 0
        # Add async_mode attribute to fix the error
        self.async_mode = False
    
    def process_request(self, request):
        """Track request start time and count"""
        request.start_time = time.time()
        self.request_count += 1
        
        # Only log cart-related requests to avoid spam
        if self._is_cart_related(request):
            print(f"\n🎬 REQUEST #{self.request_count}: {request.method} {request.path}")
            print(f"👤 User: {request.user}")
            print(f"🔐 Authenticated: {request.user.is_authenticated}")
    
    def process_response(self, request, response):
        """Track response time and log cart changes"""
        if hasattr(request, 'start_time'):
            processing_time = time.time() - request.start_time
            
            # Only log for cart-related requests
            if self._is_cart_related(request):
                self._log_cart_analysis(request, response, processing_time)
        
        return response
    
    def _is_cart_related(self, request):
        """Check if this is a cart-related request"""
        cart_paths = ['/cart/', '/add-to-cart/', '/checkout/', '/manual-add/']
        return any(path in request.path for path in cart_paths)
    
    def _log_cart_analysis(self, request, response, processing_time):
        """Perform detailed cart analysis"""
        cart = request.session.get('cart', {})
        
        print(f"⏱️  Processing Time: {processing_time:.3f}s")
        print(f"📦 Cart State: {len(cart)} products")
        
        if cart:
            total_items = sum(
                item.get('quantity', 1) if isinstance(item, dict) else int(item) 
                for item in cart.values()
            )
            print(f"📊 Total Items in Cart: {total_items}")
        
        print(f"🎯 Response: {response.status_code}")
        print("─" * 60)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.async_mode = False
    
    def process_response(self, request, response):
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Only add CSP to HTML responses
        if response.get('Content-Type', '').startswith('text/html'):
            response['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' https: data:"
        
        return response


class CartAutoSaveMiddleware(MiddlewareMixin):
    """
    Automatically save session if cart was modified
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.async_mode = False
    
    def process_response(self, request, response):
        # Check if cart exists and was potentially modified
        if 'cart' in request.session and request.session.modified:
            # Force session save to ensure cart data persists
            request.session.save()
            if self._is_cart_related(request):
                print("💾 AUTO-SAVE: Cart session saved to database")
        
        return response
    
    def _is_cart_related(self, request):
        """Check if this request could modify cart"""
        cart_modifying_paths = ['/add-to-cart/', '/manual-add/', '/cart/remove/', 
                               '/cart/increase/', '/cart/decrease/', '/cart/clear/']
        return any(path in request.path for path in cart_modifying_paths)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Log all requests for debugging purposes (optional - can be noisy)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.async_mode = False
    
    def process_request(self, request):
        # Only log specific request types to avoid too much noise
        if request.method in ['POST', 'PUT', 'DELETE']:
            print(f"📨 {request.method} Request to {request.path}")
            
            # Log POST data (excluding sensitive fields)
            if request.method == 'POST' and request.POST:
                filtered_post = {k: v for k, v in request.POST.items() 
                               if k not in ['password', 'csrfmiddlewaretoken']}
                if filtered_post:
                    print(f"📝 POST Data: {filtered_post}")


# Simple version - Use this if you're still having issues
class SimpleSessionMiddleware(MiddlewareMixin):
    """
    Simple middleware that just ensures sessions work
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.async_mode = False
    
    def process_request(self, request):
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
            print("🔄 SIMPLE MIDDLEWARE: Created session")
        
        # Debug info for cart pages
        if '/cart/' in request.path:
            cart = request.session.get('cart', {})
            print(f"🛒 CART CHECK: {len(cart)} items in cart")
    
    def process_response(self, request, response):
        # Auto-save if modified
        if request.session.modified:
            request.session.save()
            if '/cart/' in request.path or '/add-to-cart/' in request.path:
                print("💾 SIMPLE MIDDLEWARE: Session saved")
        
        return response


# Utility functions for cart debugging (can be used in views)
def debug_cart_session(session):
    """Utility function to debug cart session from anywhere"""
    cart = session.get('cart', {})
    print(f"🔍 CART DEBUG UTILITY:")
    print(f"   Session Key: {session.session_key}")
    print(f"   Cart Items: {len(cart)}")
    print(f"   Cart Data: {cart}")
    
    total_quantity = 0
    for product_id, item_data in cart.items():
        if isinstance(item_data, dict):
            quantity = item_data.get('quantity', 0)
        else:
            quantity = int(item_data) if str(item_data).isdigit() else 0
        total_quantity += quantity
        print(f"   - {product_id}: {quantity} units")
    
    print(f"   Total Quantity: {total_quantity}")
    return total_quantity


def validate_cart_data(session):
    """Validate and fix cart data structure"""
    cart = session.get('cart', {})
    fixed_count = 0
    
    for product_id, item_data in cart.items():
        # Ensure each cart item is a dictionary with quantity
        if not isinstance(item_data, dict):
            try:
                quantity = int(item_data) if str(item_data).isdigit() else 1
                cart[product_id] = {'quantity': quantity}
                fixed_count += 1
            except (ValueError, TypeError):
                # Remove invalid entries
                del cart[product_id]
                fixed_count += 1
    
    if fixed_count > 0:
        session['cart'] = cart
        session.modified = True
        print(f"🛠️  Fixed {fixed_count} cart entries")
    
    return fixed_count
