import requests

BASE_URL = "https://fakestoreapi.com"

# 🛍️ PRODUCTS
def get_all_products():
    """Fetch all products"""
    response = requests.get(f"{BASE_URL}/products")
    if response.status_code == 200:
        return response.json()
    return []

def get_product_by_id(product_id):
    """Fetch a single product"""
    response = requests.get(f"{BASE_URL}/products/{product_id}")
    if response.status_code == 200:
        return response.json()
    return None

def add_new_product(title, price, description="", category="", image=""):
    """Add a new product"""
    payload = {
        "title": title,
        "price": price,
        "description": description,
        "category": category,
        "image": image,
    }
    response = requests.post(f"{BASE_URL}/products", json=payload)
    return response.json()

def update_product(product_id, title, price, description="", category="", image=""):
    """Update product"""
    payload = {
        "title": title,
        "price": price,
        "description": description,
        "category": category,
        "image": image,
    }
    response = requests.put(f"{BASE_URL}/products/{product_id}", json=payload)
    return response.json()

def delete_product(product_id):
    """Delete a product"""
    response = requests.delete(f"{BASE_URL}/products/{product_id}")
    return response.json()

# 🛒 CARTS
def get_all_carts():
    response = requests.get(f"{BASE_URL}/carts")
    if response.status_code == 200:
        return response.json()
    return []

def add_cart(user_id, products):
    """Create a new cart"""
    payload = {"userId": user_id, "products": products}
    response = requests.post(f"{BASE_URL}/carts", json=payload)
    return response.json()

def get_cart_by_id(cart_id):
    response = requests.get(f"{BASE_URL}/carts/{cart_id}")
    if response.status_code == 200:
        return response.json()
    return None

def update_cart(cart_id, user_id, products):
    payload = {"userId": user_id, "products": products}
    response = requests.put(f"{BASE_URL}/carts/{cart_id}", json=payload)
    return response.json()

def delete_cart(cart_id):
    response = requests.delete(f"{BASE_URL}/carts/{cart_id}")
    return response.json()

# 👤 USERS
def get_all_users():
    response = requests.get(f"{BASE_URL}/users")
    if response.status_code == 200:
        return response.json()
    return []

def get_user_by_id(user_id):
    response = requests.get(f"{BASE_URL}/users/{user_id}")
    if response.status_code == 200:
        return response.json()
    return None

def add_user(username, email, password):
    payload = {"username": username, "email": email, "password": password}
    response = requests.post(f"{BASE_URL}/users", json=payload)
    return response.json()

def update_user(user_id, username, email, password):
    payload = {"username": username, "email": email, "password": password}
    response = requests.put(f"{BASE_URL}/users/{user_id}", json=payload)
    return response.json()

def delete_user(user_id):
    response = requests.delete(f"{BASE_URL}/users/{user_id}")
    return response.json()

# 🔐 LOGIN
def login_user(username, password):
    payload = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/auth/login", json=payload)
    return response.json()
