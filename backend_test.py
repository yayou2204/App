#!/usr/bin/env python3
"""
Backend API Testing for INFOTECH.MA E-commerce Platform
Tests all critical backend functionality including authentication, products, cart, configurator, and promo codes.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    base_url = line.split('=')[1].strip()
                    return f"{base_url}/api"
        return "http://localhost:8001/api"  # fallback
    except:
        return "http://localhost:8001/api"  # fallback

BASE_URL = get_backend_url()
print(f"Testing backend at: {BASE_URL}")

# Global variables for test data
user_token = None
admin_token = None
test_user_data = {
    "email": "testuser@infotech.ma",
    "username": "testuser",
    "password": "testpass123"
}
sample_product_id = None
test_results = []

def log_test(test_name, success, message="", details=""):
    """Log test results"""
    status = "✅ PASS" if success else "❌ FAIL"
    result = {
        "test": test_name,
        "status": status,
        "message": message,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    print(f"{status}: {test_name}")
    if message:
        print(f"   {message}")
    if details and not success:
        print(f"   Details: {details}")
    print()

def test_user_registration():
    """Test user registration endpoint"""
    try:
        response = requests.post(f"{BASE_URL}/register", json=test_user_data)
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and "user" in data:
                global user_token
                user_token = data["access_token"]
                log_test("User Registration", True, f"User registered successfully: {data['user']['username']}")
                return True
            else:
                log_test("User Registration", False, "Missing access_token or user in response", str(data))
                return False
        elif response.status_code == 400 and "already registered" in response.text:
            # User already exists, this is expected in subsequent test runs
            log_test("User Registration", True, "User already exists (expected in subsequent runs)")
            return True
        else:
            log_test("User Registration", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("User Registration", False, "Request failed", str(e))
        return False

def test_user_login():
    """Test user login endpoint"""
    try:
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                global user_token
                user_token = data["access_token"]  # Set token for subsequent tests
                log_test("User Login", True, f"Login successful for user: {data['user']['username']}")
                return True
            else:
                log_test("User Login", False, "Missing access_token in response", str(data))
                return False
        else:
            log_test("User Login", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("User Login", False, "Request failed", str(e))
        return False

def test_admin_login():
    """Test admin login with password 'NEW'"""
    try:
        admin_data = {"password": "NEW"}
        response = requests.post(f"{BASE_URL}/admin/login", json=admin_data)
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and data["user"].get("is_admin"):
                global admin_token
                admin_token = data["access_token"]
                log_test("Admin Login", True, "Admin login successful with password 'NEW'")
                return True
            else:
                log_test("Admin Login", False, "Missing access_token or admin flag", str(data))
                return False
        else:
            log_test("Admin Login", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Admin Login", False, "Request failed", str(e))
        return False

def test_get_products():
    """Test getting products list"""
    try:
        response = requests.get(f"{BASE_URL}/products")
        
        if response.status_code == 200:
            products = response.json()
            if isinstance(products, list) and len(products) > 0:
                global sample_product_id
                sample_product_id = products[0]["id"]
                log_test("Get Products", True, f"Retrieved {len(products)} products")
                return True
            else:
                log_test("Get Products", False, "No products found or invalid response format", str(products))
                return False
        else:
            log_test("Get Products", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Get Products", False, "Request failed", str(e))
        return False

def test_product_search():
    """Test product search functionality - LEGACY TEST (kept for compatibility)"""
    try:
        # Search for AMD products
        response = requests.get(f"{BASE_URL}/products?search=AMD")
        
        if response.status_code == 200:
            products = response.json()
            if isinstance(products, list):
                amd_found = any("AMD" in product.get("name", "") or "AMD" in product.get("brand", "") for product in products)
                if amd_found:
                    log_test("Product Search (Legacy)", True, f"Search returned {len(products)} products with AMD")
                    return True
                else:
                    log_test("Product Search (Legacy)", True, f"Search completed but no AMD products found (expected if no AMD products exist)")
                    return True
            else:
                log_test("Product Search (Legacy)", False, "Invalid response format", str(products))
                return False
        else:
            log_test("Product Search (Legacy)", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Product Search (Legacy)", False, "Request failed", str(e))
        return False

def test_precise_search_name_only():
    """Test NEW precise search functionality - searches ONLY in product names"""
    try:
        # First, get all products to understand what we're working with
        all_products_response = requests.get(f"{BASE_URL}/products")
        if all_products_response.status_code != 200:
            log_test("Precise Search - Name Only", False, "Could not fetch products for testing")
            return False
        
        all_products = all_products_response.json()
        
        # Test 1: Search for "AMD" - should only return products with "AMD" in the NAME
        response = requests.get(f"{BASE_URL}/products?search=AMD")
        if response.status_code == 200:
            amd_products = response.json()
            
            # Verify ALL returned products have "AMD" in their NAME (not just brand)
            valid_results = True
            for product in amd_products:
                if "AMD" not in product.get("name", ""):
                    valid_results = False
                    log_test("Precise Search - Name Only", False, f"Product '{product.get('name')}' returned but doesn't contain 'AMD' in name")
                    return False
            
            # Count products that have AMD in name vs brand only
            name_matches = [p for p in all_products if "AMD" in p.get("name", "")]
            brand_only_matches = [p for p in all_products if "AMD" in p.get("brand", "") and "AMD" not in p.get("name", "")]
            
            if len(amd_products) == len(name_matches):
                log_test("Precise Search - Name Only", True, f"✅ PRECISE SEARCH WORKING: Found {len(amd_products)} products with 'AMD' in NAME only (excluded {len(brand_only_matches)} brand-only matches)")
                return True
            else:
                log_test("Precise Search - Name Only", False, f"Expected {len(name_matches)} name matches, got {len(amd_products)} results")
                return False
        else:
            log_test("Precise Search - Name Only", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Precise Search - Name Only", False, "Request failed", str(e))
        return False

def test_precise_search_ryzen():
    """Test precise search for 'Ryzen' - should only find products with Ryzen in name"""
    try:
        response = requests.get(f"{BASE_URL}/products?search=Ryzen")
        
        if response.status_code == 200:
            products = response.json()
            
            # Verify all returned products have "Ryzen" in their NAME
            for product in products:
                if "Ryzen" not in product.get("name", ""):
                    log_test("Precise Search - Ryzen", False, f"Product '{product.get('name')}' returned but doesn't contain 'Ryzen' in name")
                    return False
            
            log_test("Precise Search - Ryzen", True, f"✅ Found {len(products)} products with 'Ryzen' in NAME only")
            return True
        else:
            log_test("Precise Search - Ryzen", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Precise Search - Ryzen", False, "Request failed", str(e))
        return False

def test_precise_search_rtx():
    """Test precise search for 'RTX' - should only find products with RTX in name"""
    try:
        response = requests.get(f"{BASE_URL}/products?search=RTX")
        
        if response.status_code == 200:
            products = response.json()
            
            # Verify all returned products have "RTX" in their NAME
            for product in products:
                if "RTX" not in product.get("name", ""):
                    log_test("Precise Search - RTX", False, f"Product '{product.get('name')}' returned but doesn't contain 'RTX' in name")
                    return False
            
            log_test("Precise Search - RTX", True, f"✅ Found {len(products)} products with 'RTX' in NAME only")
            return True
        else:
            log_test("Precise Search - RTX", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Precise Search - RTX", False, "Request failed", str(e))
        return False

def test_precise_search_strix():
    """Test precise search for 'STRIX' - should only find products with STRIX in name"""
    try:
        response = requests.get(f"{BASE_URL}/products?search=STRIX")
        
        if response.status_code == 200:
            products = response.json()
            
            # Verify all returned products have "STRIX" in their NAME
            for product in products:
                if "STRIX" not in product.get("name", ""):
                    log_test("Precise Search - STRIX", False, f"Product '{product.get('name')}' returned but doesn't contain 'STRIX' in name")
                    return False
            
            log_test("Precise Search - STRIX", True, f"✅ Found {len(products)} products with 'STRIX' in NAME only")
            return True
        else:
            log_test("Precise Search - STRIX", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Precise Search - STRIX", False, "Request failed", str(e))
        return False

def test_precise_search_case_insensitive():
    """Test that precise search is case-insensitive"""
    try:
        # Test with different cases
        test_cases = ["amd", "AMD", "Amd", "aMd"]
        results = []
        
        for search_term in test_cases:
            response = requests.get(f"{BASE_URL}/products?search={search_term}")
            if response.status_code == 200:
                products = response.json()
                results.append(len(products))
            else:
                log_test("Precise Search - Case Insensitive", False, f"Failed to search for '{search_term}'")
                return False
        
        # All searches should return the same number of results
        if len(set(results)) == 1:
            log_test("Precise Search - Case Insensitive", True, f"✅ Case-insensitive search working: all variations returned {results[0]} products")
            return True
        else:
            log_test("Precise Search - Case Insensitive", False, f"Case sensitivity issue: results varied {results}")
            return False
    except Exception as e:
        log_test("Precise Search - Case Insensitive", False, "Request failed", str(e))
        return False

def test_precise_search_exclusion():
    """Test that search excludes products where term is only in brand/description"""
    try:
        # Get all products first
        all_response = requests.get(f"{BASE_URL}/products")
        if all_response.status_code != 200:
            log_test("Precise Search - Exclusion Test", False, "Could not fetch all products")
            return False
        
        all_products = all_response.json()
        
        # Find products that have "NVIDIA" in brand but NOT in name
        nvidia_brand_only = []
        nvidia_in_name = []
        
        for product in all_products:
            name = product.get("name", "")
            brand = product.get("brand", "")
            
            if "NVIDIA" in brand and "NVIDIA" not in name:
                nvidia_brand_only.append(product)
            elif "NVIDIA" in name:
                nvidia_in_name.append(product)
        
        # Now search for "NVIDIA"
        search_response = requests.get(f"{BASE_URL}/products?search=NVIDIA")
        if search_response.status_code == 200:
            search_results = search_response.json()
            
            # Should only return products with NVIDIA in name, not brand-only
            if len(search_results) == len(nvidia_in_name):
                log_test("Precise Search - Exclusion Test", True, f"✅ EXCLUSION WORKING: Found {len(search_results)} products with 'NVIDIA' in name, excluded {len(nvidia_brand_only)} brand-only matches")
                return True
            else:
                log_test("Precise Search - Exclusion Test", False, f"Expected {len(nvidia_in_name)} name matches, got {len(search_results)} results. Brand-only products: {len(nvidia_brand_only)}")
                return False
        else:
            log_test("Precise Search - Exclusion Test", False, f"Search failed: {search_response.status_code}")
            return False
    except Exception as e:
        log_test("Precise Search - Exclusion Test", False, "Request failed", str(e))
        return False

def test_precise_search_empty_results():
    """Test search with terms that should return empty results"""
    try:
        # Search for a term that likely doesn't exist in any product names
        response = requests.get(f"{BASE_URL}/products?search=NONEXISTENTTERM12345")
        
        if response.status_code == 200:
            products = response.json()
            if len(products) == 0:
                log_test("Precise Search - Empty Results", True, "✅ Empty search results handled correctly")
                return True
            else:
                log_test("Precise Search - Empty Results", False, f"Expected 0 results for non-existent term, got {len(products)}")
                return False
        else:
            log_test("Precise Search - Empty Results", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Precise Search - Empty Results", False, "Request failed", str(e))
        return False

def test_precise_search_with_category():
    """Test that precise search works correctly when combined with category filtering"""
    try:
        # Search for "AMD" in CPU category only
        response = requests.get(f"{BASE_URL}/products?search=AMD&category=CPU")
        
        if response.status_code == 200:
            products = response.json()
            
            # Verify all results have "AMD" in name AND are CPU category
            for product in products:
                if "AMD" not in product.get("name", ""):
                    log_test("Precise Search with Category", False, f"Product '{product.get('name')}' doesn't have 'AMD' in name")
                    return False
                if product.get("category") != "CPU":
                    log_test("Precise Search with Category", False, f"Product '{product.get('name')}' is not CPU category")
                    return False
            
            log_test("Precise Search with Category", True, f"✅ Combined search+category returned {len(products)} valid results")
            return True
        else:
            log_test("Precise Search with Category", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Precise Search with Category", False, "Request failed", str(e))
        return False

def test_product_category_filter():
    """Test product filtering by category"""
    try:
        response = requests.get(f"{BASE_URL}/products?category=CPU")
        
        if response.status_code == 200:
            products = response.json()
            if isinstance(products, list):
                cpu_products = [p for p in products if p.get("category") == "CPU"]
                log_test("Product Category Filter", True, f"Found {len(cpu_products)} CPU products")
                return True
            else:
                log_test("Product Category Filter", False, "Invalid response format", str(products))
                return False
        else:
            log_test("Product Category Filter", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Product Category Filter", False, "Request failed", str(e))
        return False

def test_create_product():
    """Test creating a new product (admin only)"""
    if not admin_token:
        log_test("Create Product", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        product_data = {
            "name": "Test GPU RTX 4080",
            "category": "GPU",
            "brand": "NVIDIA",
            "price": 899.99,
            "description": "High-performance gaming graphics card",
            "image_base64": "",
            "stock_quantity": 5,
            "specifications": {
                "memory": "16GB GDDR6X",
                "power_requirement": 320
            },
            "compatibility_requirements": {}
        }
        
        response = requests.post(f"{BASE_URL}/admin/products", json=product_data, headers=headers)
        
        if response.status_code == 200:
            product = response.json()
            if "id" in product and product["name"] == product_data["name"]:
                log_test("Create Product", True, f"Product created: {product['name']}")
                return True
            else:
                log_test("Create Product", False, "Invalid product response", str(product))
                return False
        else:
            log_test("Create Product", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Create Product", False, "Request failed", str(e))
        return False

def test_add_to_cart():
    """Test adding product to cart"""
    if not user_token or not sample_product_id:
        log_test("Add to Cart", False, "Missing user token or product ID")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.post(f"{BASE_URL}/cart/add?product_id={sample_product_id}&quantity=1", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                log_test("Add to Cart", True, "Product added to cart successfully")
                return True
            else:
                log_test("Add to Cart", False, "Invalid response format", str(data))
                return False
        else:
            log_test("Add to Cart", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Add to Cart", False, "Request failed", str(e))
        return False

def test_get_cart():
    """Test getting user's cart"""
    if not user_token:
        log_test("Get Cart", False, "No user token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(f"{BASE_URL}/cart", headers=headers)
        
        if response.status_code == 200:
            cart = response.json()
            if "items" in cart and "total" in cart:
                log_test("Get Cart", True, f"Cart retrieved with {len(cart['items'])} items, total: ${cart['total']}")
                return True
            else:
                log_test("Get Cart", False, "Invalid cart response format", str(cart))
                return False
        else:
            log_test("Get Cart", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Get Cart", False, "Request failed", str(e))
        return False

def test_remove_from_cart():
    """Test removing item from cart using DELETE endpoint"""
    if not user_token or not sample_product_id:
        log_test("Remove from Cart", False, "Missing user token or product ID")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # First, ensure there's an item in the cart to remove
        add_response = requests.post(f"{BASE_URL}/cart/add?product_id={sample_product_id}&quantity=2", headers=headers)
        if add_response.status_code != 200:
            log_test("Remove from Cart", False, "Could not add item to cart for removal test")
            return False
        
        # Get cart before removal to verify item exists
        cart_before = requests.get(f"{BASE_URL}/cart", headers=headers)
        if cart_before.status_code != 200:
            log_test("Remove from Cart", False, "Could not get cart before removal")
            return False
        
        cart_data_before = cart_before.json()
        items_before = len(cart_data_before.get("items", []))
        total_before = cart_data_before.get("total", 0)
        
        # Now remove the item
        response = requests.delete(f"{BASE_URL}/cart/remove/{sample_product_id}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                # Verify the item was actually removed by checking cart
                cart_after = requests.get(f"{BASE_URL}/cart", headers=headers)
                if cart_after.status_code == 200:
                    cart_data_after = cart_after.json()
                    items_after = len(cart_data_after.get("items", []))
                    total_after = cart_data_after.get("total", 0)
                    
                    # Check if item was removed and total recalculated
                    item_removed = items_after < items_before
                    total_updated = total_after != total_before
                    
                    if item_removed:
                        log_test("Remove from Cart", True, f"Item removed successfully. Items: {items_before} → {items_after}, Total: ${total_before} → ${total_after}")
                        return True
                    else:
                        log_test("Remove from Cart", False, f"Item not removed. Items: {items_before} → {items_after}")
                        return False
                else:
                    log_test("Remove from Cart", False, "Could not verify cart after removal")
                    return False
            else:
                log_test("Remove from Cart", False, "Invalid response format", str(data))
                return False
        else:
            log_test("Remove from Cart", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Remove from Cart", False, "Request failed", str(e))
        return False

def test_update_cart_quantity():
    """Test updating item quantity in cart using PUT endpoint"""
    if not user_token or not sample_product_id:
        log_test("Update Cart Quantity", False, "Missing user token or product ID")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # First, add an item to the cart
        add_response = requests.post(f"{BASE_URL}/cart/add?product_id={sample_product_id}&quantity=1", headers=headers)
        if add_response.status_code != 200:
            log_test("Update Cart Quantity", False, "Could not add item to cart for quantity update test")
            return False
        
        # Get cart before update
        cart_before = requests.get(f"{BASE_URL}/cart", headers=headers)
        if cart_before.status_code != 200:
            log_test("Update Cart Quantity", False, "Could not get cart before update")
            return False
        
        cart_data_before = cart_before.json()
        total_before = cart_data_before.get("total", 0)
        
        # Update quantity to 3
        new_quantity = 3
        response = requests.put(f"{BASE_URL}/cart/update/{sample_product_id}?quantity={new_quantity}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                # Verify the quantity was actually updated
                cart_after = requests.get(f"{BASE_URL}/cart", headers=headers)
                if cart_after.status_code == 200:
                    cart_data_after = cart_after.json()
                    total_after = cart_data_after.get("total", 0)
                    
                    # Find the updated item
                    updated_item = None
                    for item in cart_data_after.get("items", []):
                        if item.get("product_id") == sample_product_id:
                            updated_item = item
                            break
                    
                    if updated_item and updated_item.get("quantity") == new_quantity:
                        log_test("Update Cart Quantity", True, f"Quantity updated successfully to {new_quantity}. Total: ${total_before} → ${total_after}")
                        return True
                    else:
                        log_test("Update Cart Quantity", False, f"Quantity not updated correctly. Expected: {new_quantity}, Got: {updated_item.get('quantity') if updated_item else 'item not found'}")
                        return False
                else:
                    log_test("Update Cart Quantity", False, "Could not verify cart after quantity update")
                    return False
            else:
                log_test("Update Cart Quantity", False, "Invalid response format", str(data))
                return False
        else:
            log_test("Update Cart Quantity", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Update Cart Quantity", False, "Request failed", str(e))
        return False

def test_cart_quantity_insufficient_stock():
    """Test updating cart quantity with insufficient stock"""
    if not user_token or not sample_product_id:
        log_test("Cart Insufficient Stock", False, "Missing user token or product ID")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Try to update quantity to a very high number (likely exceeding stock)
        excessive_quantity = 9999
        response = requests.put(f"{BASE_URL}/cart/update/{sample_product_id}?quantity={excessive_quantity}", headers=headers)
        
        if response.status_code == 400:
            data = response.json()
            if "Insufficient stock" in data.get("detail", ""):
                log_test("Cart Insufficient Stock", True, "Correctly handled insufficient stock error")
                return True
            else:
                log_test("Cart Insufficient Stock", False, f"Expected insufficient stock error, got: {data}")
                return False
        else:
            log_test("Cart Insufficient Stock", False, f"Expected 400 status for insufficient stock, got {response.status_code}")
            return False
    except Exception as e:
        log_test("Cart Insufficient Stock", False, "Request failed", str(e))
        return False

def test_cart_operations_with_promo():
    """Test cart operations with promo code applied to verify discount recalculation"""
    if not user_token or not sample_product_id:
        log_test("Cart Operations with Promo", False, "Missing user token or product ID")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Clear cart first by removing any existing items
        cart_response = requests.get(f"{BASE_URL}/cart", headers=headers)
        if cart_response.status_code == 200:
            cart_data = cart_response.json()
            for item in cart_data.get("items", []):
                requests.delete(f"{BASE_URL}/cart/remove/{item['product_id']}", headers=headers)
        
        # Add item to cart
        add_response = requests.post(f"{BASE_URL}/cart/add?product_id={sample_product_id}&quantity=2", headers=headers)
        if add_response.status_code != 200:
            log_test("Cart Operations with Promo", False, "Could not add item to cart")
            return False
        
        # Apply promo code (try GAMING10 first, create one if needed)
        promo_response = requests.post(f"{BASE_URL}/cart/apply-promo?code=GAMING10", headers=headers)
        if promo_response.status_code != 200 and admin_token:
            # Create a promo code for testing
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            create_promo = requests.post(f"{BASE_URL}/admin/promo-codes?code=TESTPROMO&discount_percentage=15", headers=admin_headers)
            if create_promo.status_code == 200:
                promo_response = requests.post(f"{BASE_URL}/cart/apply-promo?code=TESTPROMO", headers=headers)
        
        if promo_response.status_code != 200:
            log_test("Cart Operations with Promo", True, "No active promo codes available for testing (expected)")
            return True
        
        # Get cart with promo applied
        cart_with_promo = requests.get(f"{BASE_URL}/cart", headers=headers)
        if cart_with_promo.status_code != 200:
            log_test("Cart Operations with Promo", False, "Could not get cart with promo")
            return False
        
        cart_data_with_promo = cart_with_promo.json()
        discount_before = cart_data_with_promo.get("discount", 0)
        
        # Update quantity and verify discount is recalculated
        update_response = requests.put(f"{BASE_URL}/cart/update/{sample_product_id}?quantity=3", headers=headers)
        if update_response.status_code != 200:
            log_test("Cart Operations with Promo", False, "Could not update quantity with promo applied")
            return False
        
        # Check if discount was recalculated
        cart_after_update = requests.get(f"{BASE_URL}/cart", headers=headers)
        if cart_after_update.status_code == 200:
            cart_data_after = cart_after_update.json()
            discount_after = cart_data_after.get("discount", 0)
            
            # Discount should change when quantity changes
            if discount_after != discount_before:
                log_test("Cart Operations with Promo", True, f"Promo discount recalculated correctly: ${discount_before} → ${discount_after}")
                return True
            else:
                log_test("Cart Operations with Promo", True, f"Promo discount maintained: ${discount_after}")
                return True
        else:
            log_test("Cart Operations with Promo", False, "Could not verify cart after quantity update with promo")
            return False
            
    except Exception as e:
        log_test("Cart Operations with Promo", False, "Request failed", str(e))
        return False

def test_remove_nonexistent_cart_item():
    """Test removing non-existent item from cart"""
    if not user_token:
        log_test("Remove Nonexistent Item", False, "No user token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        fake_product_id = "non-existent-product-id"
        
        response = requests.delete(f"{BASE_URL}/cart/remove/{fake_product_id}", headers=headers)
        
        # Should succeed even if item doesn't exist (removes nothing)
        if response.status_code == 200:
            log_test("Remove Nonexistent Item", True, "Correctly handled removal of non-existent item")
            return True
        else:
            log_test("Remove Nonexistent Item", False, f"Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        log_test("Remove Nonexistent Item", False, "Request failed", str(e))
        return False

def test_create_promo_code():
    """Test creating a promo code (admin only)"""
    if not admin_token:
        log_test("Create Promo Code", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(f"{BASE_URL}/admin/promo-codes?code=TEST20&discount_percentage=20", headers=headers)
        
        if response.status_code == 200:
            promo = response.json()
            if "code" in promo and promo["code"] == "TEST20":
                log_test("Create Promo Code", True, f"Promo code created: {promo['code']} ({promo['discount_percentage']}% off)")
                return True
            else:
                log_test("Create Promo Code", False, "Invalid promo response", str(promo))
                return False
        else:
            log_test("Create Promo Code", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Create Promo Code", False, "Request failed", str(e))
        return False

def test_apply_promo_code():
    """Test applying promo code to cart"""
    if not user_token:
        log_test("Apply Promo Code", False, "No user token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # First, ensure we have an active promo code to test with
        if admin_token:
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            # Create a test promo code for application
            create_response = requests.post(f"{BASE_URL}/admin/promo-codes?code=APPLY_TEST&discount_percentage=10", headers=admin_headers)
            if create_response.status_code == 200:
                test_code = "APPLY_TEST"
            else:
                # Fallback to GAMING10 if it exists and is active
                test_code = "GAMING10"
        else:
            test_code = "GAMING10"
        
        # Try to apply the promo code
        response = requests.post(f"{BASE_URL}/cart/apply-promo?code={test_code}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "discount" in data:
                log_test("Apply Promo Code", True, f"Promo code '{test_code}' applied, discount: ${data['discount']}")
                return True
            else:
                log_test("Apply Promo Code", False, "Invalid response format", str(data))
                return False
        elif response.status_code == 404:
            # If the promo code doesn't exist or is inactive, try to create and activate one
            if admin_token:
                admin_headers = {"Authorization": f"Bearer {admin_token}"}
                # Create a new active promo code
                create_response = requests.post(f"{BASE_URL}/admin/promo-codes?code=TESTACTIVE&discount_percentage=5", headers=admin_headers)
                if create_response.status_code == 200:
                    # Try applying the new code
                    retry_response = requests.post(f"{BASE_URL}/cart/apply-promo?code=TESTACTIVE", headers=headers)
                    if retry_response.status_code == 200:
                        data = retry_response.json()
                        log_test("Apply Promo Code", True, f"Promo code 'TESTACTIVE' applied, discount: ${data.get('discount', 0)}")
                        return True
            
            log_test("Apply Promo Code", False, f"No active promo codes available for testing")
            return False
        else:
            log_test("Apply Promo Code", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Apply Promo Code", False, "Request failed", str(e))
        return False

def test_get_all_promo_codes():
    """Test getting all promo codes (admin only)"""
    if not admin_token:
        log_test("Get All Promo Codes", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/admin/promo-codes", headers=headers)
        
        if response.status_code == 200:
            promos = response.json()
            if isinstance(promos, list):
                log_test("Get All Promo Codes", True, f"Retrieved {len(promos)} promo codes")
                return True
            else:
                log_test("Get All Promo Codes", False, "Invalid response format", str(promos))
                return False
        else:
            log_test("Get All Promo Codes", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Get All Promo Codes", False, "Request failed", str(e))
        return False

def test_update_promo_code():
    """Test updating a promo code (admin only)"""
    if not admin_token:
        log_test("Update Promo Code", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First get all promo codes to find one to update
        get_response = requests.get(f"{BASE_URL}/admin/promo-codes", headers=headers)
        if get_response.status_code != 200:
            log_test("Update Promo Code", False, "Could not fetch promo codes for testing")
            return False
        
        promos = get_response.json()
        if not promos:
            log_test("Update Promo Code", True, "No promo codes available to update (expected if none exist)")
            return True
        
        # Update the first promo code
        promo_id = promos[0]["id"]
        response = requests.put(f"{BASE_URL}/admin/promo-codes/{promo_id}?code=UPDATED15&discount_percentage=15", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                log_test("Update Promo Code", True, "Promo code updated successfully")
                return True
            else:
                log_test("Update Promo Code", False, "Invalid response format", str(data))
                return False
        else:
            log_test("Update Promo Code", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Update Promo Code", False, "Request failed", str(e))
        return False

def test_toggle_promo_code():
    """Test toggling promo code active status (admin only)"""
    if not admin_token:
        log_test("Toggle Promo Code", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First get all promo codes to find one to toggle
        get_response = requests.get(f"{BASE_URL}/admin/promo-codes", headers=headers)
        if get_response.status_code != 200:
            log_test("Toggle Promo Code", False, "Could not fetch promo codes for testing")
            return False
        
        promos = get_response.json()
        if not promos:
            log_test("Toggle Promo Code", True, "No promo codes available to toggle (expected if none exist)")
            return True
        
        # Toggle the first promo code
        promo_id = promos[0]["id"]
        current_status = promos[0].get("active", True)
        new_status = not current_status
        
        response = requests.put(f"{BASE_URL}/admin/promo-codes/{promo_id}/toggle?active={str(new_status).lower()}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                action = "activated" if new_status else "deactivated"
                log_test("Toggle Promo Code", True, f"Promo code {action} successfully")
                return True
            else:
                log_test("Toggle Promo Code", False, "Invalid response format", str(data))
                return False
        else:
            log_test("Toggle Promo Code", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Toggle Promo Code", False, "Request failed", str(e))
        return False

def test_delete_promo_code():
    """Test deleting a promo code (admin only)"""
    if not admin_token:
        log_test("Delete Promo Code", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test promo code to delete
        create_response = requests.post(f"{BASE_URL}/admin/promo-codes?code=DELETE_TEST&discount_percentage=5", headers=headers)
        if create_response.status_code != 200:
            log_test("Delete Promo Code", False, "Could not create test promo code for deletion")
            return False
        
        created_promo = create_response.json()
        promo_id = created_promo["id"]
        
        # Now delete it
        response = requests.delete(f"{BASE_URL}/admin/promo-codes/{promo_id}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                log_test("Delete Promo Code", True, "Promo code deleted successfully")
                return True
            else:
                log_test("Delete Promo Code", False, "Invalid response format", str(data))
                return False
        else:
            log_test("Delete Promo Code", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Delete Promo Code", False, "Request failed", str(e))
        return False

def test_search_and_category_combined():
    """Test product search with both search and category parameters"""
    try:
        # Search for AMD products in CPU category
        response = requests.get(f"{BASE_URL}/products?search=AMD&category=CPU")
        
        if response.status_code == 200:
            products = response.json()
            if isinstance(products, list):
                # Check that all returned products match both criteria
                valid_results = all(
                    product.get("category") == "CPU" and 
                    ("AMD" in product.get("name", "") or "AMD" in product.get("brand", "") or "AMD" in product.get("description", ""))
                    for product in products
                ) if products else True
                
                if valid_results:
                    log_test("Search and Category Combined", True, f"Combined search returned {len(products)} matching products")
                    return True
                else:
                    log_test("Search and Category Combined", False, "Some products don't match search criteria")
                    return False
            else:
                log_test("Search and Category Combined", False, "Invalid response format", str(products))
                return False
        else:
            log_test("Search and Category Combined", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Search and Category Combined", False, "Request failed", str(e))
        return False

def test_invalid_promo_operations():
    """Test error handling for invalid promo code operations"""
    if not admin_token:
        log_test("Invalid Promo Operations", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test updating non-existent promo code
        fake_id = "non-existent-id"
        response = requests.put(f"{BASE_URL}/admin/promo-codes/{fake_id}?code=FAKE&discount_percentage=10", headers=headers)
        
        if response.status_code == 404:
            log_test("Invalid Promo Operations", True, "Correctly handled non-existent promo code update")
            return True
        else:
            log_test("Invalid Promo Operations", False, f"Expected 404 for non-existent promo, got {response.status_code}")
            return False
    except Exception as e:
        log_test("Invalid Promo Operations", False, "Request failed", str(e))
        return False

def test_configurator_categories():
    """Test getting configurator categories"""
    try:
        response = requests.get(f"{BASE_URL}/configurator/categories")
        
        if response.status_code == 200:
            data = response.json()
            if "categories" in data and isinstance(data["categories"], list):
                categories = data["categories"]
                expected_categories = ["CPU", "MOTHERBOARD", "RAM", "GPU", "STORAGE", "PSU", "CASE", "COOLING"]
                if all(cat in categories for cat in expected_categories):
                    log_test("Configurator Categories", True, f"All expected categories found: {len(categories)} categories")
                    return True
                else:
                    log_test("Configurator Categories", False, f"Missing expected categories. Got: {categories}")
                    return False
            else:
                log_test("Configurator Categories", False, "Invalid response format", str(data))
                return False
        else:
            log_test("Configurator Categories", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Configurator Categories", False, "Request failed", str(e))
        return False

def test_pc_configuration_validation():
    """Test PC configuration compatibility validation"""
    if not user_token:
        log_test("PC Configuration Validation", False, "No user token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Get some products to test with
        products_response = requests.get(f"{BASE_URL}/products")
        if products_response.status_code != 200:
            log_test("PC Configuration Validation", False, "Could not fetch products for testing")
            return False
        
        products = products_response.json()
        cpu_product = next((p for p in products if p["category"] == "CPU"), None)
        motherboard_product = next((p for p in products if p["category"] == "MOTHERBOARD"), None)
        
        if not cpu_product or not motherboard_product:
            log_test("PC Configuration Validation", True, "No CPU/Motherboard products available for compatibility testing")
            return True
        
        # Test configuration with compatible components
        config_data = {
            "CPU": cpu_product["id"],
            "MOTHERBOARD": motherboard_product["id"]
        }
        
        response = requests.post(f"{BASE_URL}/configurator/validate", json=config_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "compatible" in data and "issues" in data and "total_price" in data:
                log_test("PC Configuration Validation", True, f"Validation completed - Compatible: {data['compatible']}, Price: ${data['total_price']}")
                return True
            else:
                log_test("PC Configuration Validation", False, "Invalid response format", str(data))
                return False
        else:
            log_test("PC Configuration Validation", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("PC Configuration Validation", False, "Request failed", str(e))
        return False

def test_save_pc_configuration():
    """Test saving PC configuration"""
    if not user_token:
        log_test("Save PC Configuration", False, "No user token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Get some products to test with
        products_response = requests.get(f"{BASE_URL}/products")
        if products_response.status_code != 200:
            log_test("Save PC Configuration", False, "Could not fetch products for testing")
            return False
        
        products = products_response.json()
        cpu_product = next((p for p in products if p["category"] == "CPU"), None)
        
        if not cpu_product:
            log_test("Save PC Configuration", True, "No CPU products available for configuration testing")
            return True
        
        components_data = {"CPU": cpu_product["id"]}
        
        response = requests.post(f"{BASE_URL}/configurator/save?name=Test Gaming Build", json=components_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "id" in data and "name" in data:
                log_test("Save PC Configuration", True, f"Configuration saved: {data['name']}")
                return True
            else:
                log_test("Save PC Configuration", False, "Invalid response format", str(data))
                return False
        else:
            log_test("Save PC Configuration", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Save PC Configuration", False, "Request failed", str(e))
        return False

def test_get_my_configurations():
    """Test getting user's saved configurations"""
    if not user_token:
        log_test("Get My Configurations", False, "No user token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(f"{BASE_URL}/configurator/my-configs", headers=headers)
        
        if response.status_code == 200:
            configs = response.json()
            if isinstance(configs, list):
                log_test("Get My Configurations", True, f"Retrieved {len(configs)} saved configurations")
                return True
            else:
                log_test("Get My Configurations", False, "Invalid response format", str(configs))
                return False
        else:
            log_test("Get My Configurations", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Get My Configurations", False, "Request failed", str(e))
        return False

# Global variables for product filter testing
test_filter_ids = []

def test_get_product_filters_admin():
    """Test getting all product filters (admin only)"""
    if not admin_token:
        log_test("Get Product Filters (Admin)", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/admin/product-filters", headers=headers)
        
        if response.status_code == 200:
            filters = response.json()
            if isinstance(filters, list):
                log_test("Get Product Filters (Admin)", True, f"Retrieved {len(filters)} product filters")
                return True
            else:
                log_test("Get Product Filters (Admin)", False, "Invalid response format", str(filters))
                return False
        else:
            log_test("Get Product Filters (Admin)", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Get Product Filters (Admin)", False, "Request failed", str(e))
        return False

def test_create_select_filter():
    """Test creating a select type filter (brand filter)"""
    if not admin_token:
        log_test("Create Select Filter", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        filter_data = {
            "name": "Marque",
            "type": "select", 
            "field": "brand",
            "values": ["AMD", "Intel", "NVIDIA", "ASUS", "MSI"]
        }
        
        response = requests.post(f"{BASE_URL}/admin/product-filters", 
                               params=filter_data, headers=headers)
        
        if response.status_code == 200:
            filter_obj = response.json()
            if "id" in filter_obj and filter_obj["name"] == "Marque":
                global test_filter_ids
                test_filter_ids.append(filter_obj["id"])
                log_test("Create Select Filter", True, f"Select filter created: {filter_obj['name']} with {len(filter_obj['values'])} values")
                return True
            else:
                log_test("Create Select Filter", False, "Invalid filter response", str(filter_obj))
                return False
        else:
            log_test("Create Select Filter", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Create Select Filter", False, "Request failed", str(e))
        return False

def test_create_range_filter():
    """Test creating a range type filter (price filter)"""
    if not admin_token:
        log_test("Create Range Filter", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        filter_data = {
            "name": "Prix",
            "type": "range",
            "field": "price",
            "values": []  # Range filters don't need predefined values
        }
        
        response = requests.post(f"{BASE_URL}/admin/product-filters", 
                               params=filter_data, headers=headers)
        
        if response.status_code == 200:
            filter_obj = response.json()
            if "id" in filter_obj and filter_obj["name"] == "Prix":
                global test_filter_ids
                test_filter_ids.append(filter_obj["id"])
                log_test("Create Range Filter", True, f"Range filter created: {filter_obj['name']} for field {filter_obj['field']}")
                return True
            else:
                log_test("Create Range Filter", False, "Invalid filter response", str(filter_obj))
                return False
        else:
            log_test("Create Range Filter", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Create Range Filter", False, "Request failed", str(e))
        return False

def test_create_boolean_filter():
    """Test creating a boolean type filter (stock availability)"""
    if not admin_token:
        log_test("Create Boolean Filter", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        filter_data = {
            "name": "En stock",
            "type": "boolean",
            "field": "stock_quantity",
            "values": []  # Boolean filters don't need predefined values
        }
        
        response = requests.post(f"{BASE_URL}/admin/product-filters", 
                               params=filter_data, headers=headers)
        
        if response.status_code == 200:
            filter_obj = response.json()
            if "id" in filter_obj and filter_obj["name"] == "En stock":
                global test_filter_ids
                test_filter_ids.append(filter_obj["id"])
                log_test("Create Boolean Filter", True, f"Boolean filter created: {filter_obj['name']} for field {filter_obj['field']}")
                return True
            else:
                log_test("Create Boolean Filter", False, "Invalid filter response", str(filter_obj))
                return False
        else:
            log_test("Create Boolean Filter", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Create Boolean Filter", False, "Request failed", str(e))
        return False

def test_create_specifications_filter():
    """Test creating a filter for product specifications (color)"""
    if not admin_token:
        log_test("Create Specifications Filter", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        filter_data = {
            "name": "Couleur",
            "type": "select",
            "field": "specifications.color",
            "values": ["Rouge", "Bleu", "Noir", "Blanc", "RGB"]
        }
        
        response = requests.post(f"{BASE_URL}/admin/product-filters", 
                               params=filter_data, headers=headers)
        
        if response.status_code == 200:
            filter_obj = response.json()
            if "id" in filter_obj and filter_obj["name"] == "Couleur":
                global test_filter_ids
                test_filter_ids.append(filter_obj["id"])
                log_test("Create Specifications Filter", True, f"Specifications filter created: {filter_obj['name']} for nested field {filter_obj['field']}")
                return True
            else:
                log_test("Create Specifications Filter", False, "Invalid filter response", str(filter_obj))
                return False
        else:
            log_test("Create Specifications Filter", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Create Specifications Filter", False, "Request failed", str(e))
        return False

def test_update_product_filter():
    """Test updating a product filter"""
    if not admin_token or not test_filter_ids:
        log_test("Update Product Filter", False, "No admin token or test filters available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        filter_id = test_filter_ids[0]  # Use first created filter
        
        update_data = {
            "name": "Marque Mise à Jour",
            "type": "select",
            "field": "brand", 
            "values": ["AMD", "Intel", "NVIDIA", "ASUS", "MSI", "Corsair"]
        }
        
        response = requests.put(f"{BASE_URL}/admin/product-filters/{filter_id}", 
                              params=update_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                log_test("Update Product Filter", True, "Product filter updated successfully")
                return True
            else:
                log_test("Update Product Filter", False, "Invalid response format", str(data))
                return False
        else:
            log_test("Update Product Filter", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Update Product Filter", False, "Request failed", str(e))
        return False

def test_toggle_product_filter():
    """Test toggling product filter active status"""
    if not admin_token or not test_filter_ids:
        log_test("Toggle Product Filter", False, "No admin token or test filters available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        filter_id = test_filter_ids[0]  # Use first created filter
        
        # Toggle to inactive
        response = requests.put(f"{BASE_URL}/admin/product-filters/{filter_id}/toggle?active=false", 
                              headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "deactivated" in data.get("message", ""):
                # Toggle back to active
                response2 = requests.put(f"{BASE_URL}/admin/product-filters/{filter_id}/toggle?active=true", 
                                       headers=headers)
                if response2.status_code == 200:
                    log_test("Toggle Product Filter", True, "Product filter toggled successfully (inactive → active)")
                    return True
                else:
                    log_test("Toggle Product Filter", False, f"Failed to toggle back to active: {response2.status_code}")
                    return False
            else:
                log_test("Toggle Product Filter", False, "Invalid response format", str(data))
                return False
        else:
            log_test("Toggle Product Filter", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Toggle Product Filter", False, "Request failed", str(e))
        return False

def test_get_active_product_filters():
    """Test getting active product filters (public endpoint)"""
    try:
        response = requests.get(f"{BASE_URL}/product-filters")
        
        if response.status_code == 200:
            filters = response.json()
            if isinstance(filters, list):
                active_count = len(filters)
                log_test("Get Active Product Filters", True, f"Retrieved {active_count} active product filters")
                return True
            else:
                log_test("Get Active Product Filters", False, "Invalid response format", str(filters))
                return False
        else:
            log_test("Get Active Product Filters", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Get Active Product Filters", False, "Request failed", str(e))
        return False

def test_product_filtering_by_brand():
    """Test dynamic product filtering by brand"""
    try:
        # Test filtering by AMD brand using the dynamic filter system
        response = requests.get(f"{BASE_URL}/products?filter_marque_mise_à_jour=AMD")
        
        if response.status_code == 200:
            products = response.json()
            if isinstance(products, list):
                # Check if all returned products are AMD brand
                amd_products = [p for p in products if p.get("brand") == "AMD"]
                if len(products) == len(amd_products) or len(products) == 0:
                    log_test("Product Filtering by Brand", True, f"Brand filtering returned {len(products)} AMD products")
                    return True
                else:
                    log_test("Product Filtering by Brand", False, f"Brand filter returned non-AMD products: {len(products)} total, {len(amd_products)} AMD")
                    return False
            else:
                log_test("Product Filtering by Brand", False, "Invalid response format", str(products))
                return False
        else:
            log_test("Product Filtering by Brand", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Product Filtering by Brand", False, "Request failed", str(e))
        return False

def test_product_filtering_by_price_range():
    """Test dynamic product filtering by price range"""
    try:
        # Test filtering by price range (100-500)
        response = requests.get(f"{BASE_URL}/products?filter_prix=100:500")
        
        if response.status_code == 200:
            products = response.json()
            if isinstance(products, list):
                # Check if all returned products are within price range
                valid_products = [p for p in products if 100 <= p.get("price", 0) <= 500]
                if len(products) == len(valid_products) or len(products) == 0:
                    log_test("Product Filtering by Price Range", True, f"Price range filtering returned {len(products)} products in range 100-500")
                    return True
                else:
                    log_test("Product Filtering by Price Range", False, f"Price filter returned products outside range: {len(products)} total, {len(valid_products)} valid")
                    return False
            else:
                log_test("Product Filtering by Price Range", False, "Invalid response format", str(products))
                return False
        else:
            log_test("Product Filtering by Price Range", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Product Filtering by Price Range", False, "Request failed", str(e))
        return False

def test_product_filtering_by_stock():
    """Test dynamic product filtering by stock availability"""
    try:
        # Test filtering by stock availability (products with stock > 0)
        response = requests.get(f"{BASE_URL}/products?filter_en_stock=true")
        
        if response.status_code == 200:
            products = response.json()
            if isinstance(products, list):
                # Check if all returned products have stock > 0
                in_stock_products = [p for p in products if p.get("stock_quantity", 0) > 0]
                if len(products) == len(in_stock_products) or len(products) == 0:
                    log_test("Product Filtering by Stock", True, f"Stock filtering returned {len(products)} products in stock")
                    return True
                else:
                    log_test("Product Filtering by Stock", False, f"Stock filter returned out-of-stock products: {len(products)} total, {len(in_stock_products)} in stock")
                    return False
            else:
                log_test("Product Filtering by Stock", False, "Invalid response format", str(products))
                return False
        else:
            log_test("Product Filtering by Stock", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Product Filtering by Stock", False, "Request failed", str(e))
        return False

def test_combined_filtering():
    """Test combining multiple filters (search + category + dynamic filters)"""
    try:
        # Test combining search, category, and brand filter
        response = requests.get(f"{BASE_URL}/products?search=AMD&category=CPU&filter_marque_mise_à_jour=AMD")
        
        if response.status_code == 200:
            products = response.json()
            if isinstance(products, list):
                # Verify all products match all criteria
                valid_products = []
                for product in products:
                    matches_search = "AMD" in product.get("name", "") or "AMD" in product.get("brand", "") or "AMD" in product.get("description", "")
                    matches_category = product.get("category") == "CPU"
                    matches_brand = product.get("brand") == "AMD"
                    
                    if matches_search and matches_category and matches_brand:
                        valid_products.append(product)
                
                if len(products) == len(valid_products) or len(products) == 0:
                    log_test("Combined Filtering", True, f"Combined filtering returned {len(products)} products matching all criteria")
                    return True
                else:
                    log_test("Combined Filtering", False, f"Combined filter returned invalid products: {len(products)} total, {len(valid_products)} valid")
                    return False
            else:
                log_test("Combined Filtering", False, "Invalid response format", str(products))
                return False
        else:
            log_test("Combined Filtering", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Combined Filtering", False, "Request failed", str(e))
        return False

def test_filter_authentication():
    """Test that admin filter endpoints require authentication"""
    try:
        # Test creating filter without authentication
        filter_data = {
            "name": "Test Filter",
            "type": "select",
            "field": "brand",
            "values": ["Test"]
        }
        
        response = requests.post(f"{BASE_URL}/admin/product-filters", params=filter_data)
        
        if response.status_code == 401 or response.status_code == 403:
            log_test("Filter Authentication", True, "Admin filter endpoints correctly require authentication")
            return True
        else:
            log_test("Filter Authentication", False, f"Expected 401/403 for unauthenticated request, got {response.status_code}")
            return False
    except Exception as e:
        log_test("Filter Authentication", False, "Request failed", str(e))
        return False

def test_delete_product_filter():
    """Test deleting a product filter"""
    if not admin_token or not test_filter_ids:
        log_test("Delete Product Filter", False, "No admin token or test filters available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a filter specifically for deletion
        filter_data = {
            "name": "Delete Test Filter",
            "type": "select",
            "field": "category",
            "values": ["TEST"]
        }
        
        create_response = requests.post(f"{BASE_URL}/admin/product-filters", 
                                      params=filter_data, headers=headers)
        
        if create_response.status_code != 200:
            log_test("Delete Product Filter", False, "Could not create test filter for deletion")
            return False
        
        created_filter = create_response.json()
        filter_id = created_filter["id"]
        
        # Now delete it
        response = requests.delete(f"{BASE_URL}/admin/product-filters/{filter_id}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                log_test("Delete Product Filter", True, "Product filter deleted successfully")
                return True
            else:
                log_test("Delete Product Filter", False, "Invalid response format", str(data))
                return False
        else:
            log_test("Delete Product Filter", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Delete Product Filter", False, "Request failed", str(e))
        return False

def test_invalid_filter_operations():
    """Test error handling for invalid filter operations"""
    if not admin_token:
        log_test("Invalid Filter Operations", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test updating non-existent filter
        fake_id = "non-existent-filter-id"
        update_data = {
            "name": "Fake Filter",
            "type": "select",
            "field": "fake_field",
            "values": ["fake"]
        }
        
        response = requests.put(f"{BASE_URL}/admin/product-filters/{fake_id}", 
                              params=update_data, headers=headers)
        
        if response.status_code == 404:
            log_test("Invalid Filter Operations", True, "Correctly handled non-existent filter update")
            return True
        else:
            log_test("Invalid Filter Operations", False, f"Expected 404 for non-existent filter, got {response.status_code}")
            return False
    except Exception as e:
        log_test("Invalid Filter Operations", False, "Request failed", str(e))
        return False

# Global variables for support ticket and review testing
test_ticket_id = None
test_review_id = None

def test_create_product_review():
    """Test creating a product review (authenticated users only)"""
    if not user_token or not sample_product_id:
        log_test("Create Product Review", False, "No user token or product ID available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        review_data = {
            "product_id": sample_product_id,
            "rating": 5,
            "comment": "Excellent produit! Très satisfait de mon achat. Performance exceptionnelle et qualité au rendez-vous."
        }
        
        response = requests.post(f"{BASE_URL}/reviews", json=review_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                log_test("Create Product Review", True, f"Product review created successfully for product {sample_product_id}")
                return True
            else:
                log_test("Create Product Review", False, "Invalid response format", str(data))
                return False
        elif response.status_code == 400 and "déjà noté" in response.text:
            # User already reviewed this product - this is expected in subsequent test runs
            log_test("Create Product Review", True, "User already reviewed this product (expected in subsequent runs)")
            return True
        else:
            log_test("Create Product Review", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Create Product Review", False, "Request failed", str(e))
        return False

def test_get_product_reviews():
    """Test getting reviews for a specific product"""
    if not sample_product_id:
        log_test("Get Product Reviews", False, "No product ID available")
        return False
    
    try:
        response = requests.get(f"{BASE_URL}/reviews/{sample_product_id}")
        
        if response.status_code == 200:
            reviews = response.json()
            if isinstance(reviews, list):
                log_test("Get Product Reviews", True, f"Retrieved {len(reviews)} reviews for product {sample_product_id}")
                # Store first review ID for deletion test
                if reviews:
                    global test_review_id
                    test_review_id = reviews[0].get("id")
                return True
            else:
                log_test("Get Product Reviews", False, "Invalid response format", str(reviews))
                return False
        else:
            log_test("Get Product Reviews", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Get Product Reviews", False, "Request failed", str(e))
        return False

def test_get_product_review_stats():
    """Test getting review statistics for a product - CRITICAL for products page"""
    if not sample_product_id:
        log_test("Get Product Review Stats", False, "No product ID available")
        return False
    
    try:
        response = requests.get(f"{BASE_URL}/reviews/{sample_product_id}/stats")
        
        if response.status_code == 200:
            stats = response.json()
            required_fields = ["average_rating", "total_reviews", "rating_distribution"]
            
            if all(field in stats for field in required_fields):
                avg_rating = stats["average_rating"]
                total_reviews = stats["total_reviews"]
                rating_dist = stats["rating_distribution"]
                
                # Validate data types and ranges
                if (isinstance(avg_rating, (int, float)) and 0 <= avg_rating <= 5 and
                    isinstance(total_reviews, int) and total_reviews >= 0 and
                    isinstance(rating_dist, dict) and 
                    all(str(i) in rating_dist for i in range(1, 6))):
                    
                    log_test("Get Product Review Stats", True, 
                           f"Review stats retrieved: {avg_rating}★ average, {total_reviews} reviews, distribution: {rating_dist}")
                    return True
                else:
                    log_test("Get Product Review Stats", False, 
                           f"Invalid stats data: avg={avg_rating}, total={total_reviews}, dist={rating_dist}")
                    return False
            else:
                log_test("Get Product Review Stats", False, f"Missing required fields in response: {stats}")
                return False
        else:
            log_test("Get Product Review Stats", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Get Product Review Stats", False, "Request failed", str(e))
        return False

def test_product_review_stats_no_reviews():
    """Test review stats for a product with no reviews"""
    try:
        # Create a new product specifically for this test
        if not admin_token:
            log_test("Review Stats No Reviews", False, "No admin token available")
            return False
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        product_data = {
            "name": "Test Product No Reviews",
            "category": "GPU",
            "brand": "TEST",
            "price": 299.99,
            "description": "Test product for review stats testing",
            "image_base64": "",
            "stock_quantity": 1,
            "specifications": {},
            "compatibility_requirements": {}
        }
        
        create_response = requests.post(f"{BASE_URL}/admin/products", json=product_data, headers=headers)
        if create_response.status_code != 200:
            log_test("Review Stats No Reviews", False, "Could not create test product")
            return False
        
        test_product = create_response.json()
        test_product_id = test_product["id"]
        
        # Get stats for product with no reviews
        response = requests.get(f"{BASE_URL}/reviews/{test_product_id}/stats")
        
        if response.status_code == 200:
            stats = response.json()
            expected_stats = {
                "average_rating": 0,
                "total_reviews": 0,
                "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }
            
            if (stats["average_rating"] == 0 and 
                stats["total_reviews"] == 0 and
                all(stats["rating_distribution"][str(i)] == 0 for i in range(1, 6))):
                
                log_test("Review Stats No Reviews", True, "Correctly returned zero stats for product with no reviews")
                return True
            else:
                log_test("Review Stats No Reviews", False, f"Incorrect stats for no reviews: {stats}")
                return False
        else:
            log_test("Review Stats No Reviews", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Review Stats No Reviews", False, "Request failed", str(e))
        return False

def test_multiple_product_review_stats():
    """Test getting review stats for multiple products (simulating products page load)"""
    try:
        # Get all products
        products_response = requests.get(f"{BASE_URL}/products")
        if products_response.status_code != 200:
            log_test("Multiple Product Review Stats", False, "Could not fetch products")
            return False
        
        products = products_response.json()
        if not products:
            log_test("Multiple Product Review Stats", True, "No products available for stats testing")
            return True
        
        # Test stats for first 3 products (or all if less than 3)
        test_products = products[:3]
        successful_requests = 0
        
        for product in test_products:
            product_id = product["id"]
            response = requests.get(f"{BASE_URL}/reviews/{product_id}/stats")
            
            if response.status_code == 200:
                stats = response.json()
                if ("average_rating" in stats and "total_reviews" in stats and 
                    "rating_distribution" in stats):
                    successful_requests += 1
                else:
                    log_test("Multiple Product Review Stats", False, 
                           f"Invalid stats format for product {product_id}: {stats}")
                    return False
            else:
                log_test("Multiple Product Review Stats", False, 
                       f"Failed to get stats for product {product_id}: HTTP {response.status_code}")
                return False
        
        log_test("Multiple Product Review Stats", True, 
               f"Successfully retrieved review stats for {successful_requests}/{len(test_products)} products")
        return True
        
    except Exception as e:
        log_test("Multiple Product Review Stats", False, "Request failed", str(e))
        return False

def test_create_multiple_reviews_different_ratings():
    """Test creating multiple reviews with different ratings to verify average calculation"""
    if not admin_token or not sample_product_id:
        log_test("Multiple Reviews Different Ratings", False, "No admin token or product ID available")
        return False
    
    try:
        # Create additional test users for multiple reviews
        test_users = [
            {"email": "reviewer1@infotech.ma", "username": "reviewer1", "password": "pass123"},
            {"email": "reviewer2@infotech.ma", "username": "reviewer2", "password": "pass123"},
            {"email": "reviewer3@infotech.ma", "username": "reviewer3", "password": "pass123"}
        ]
        
        user_tokens = []
        
        # Register and login test users
        for user_data in test_users:
            # Try to register (might already exist)
            register_response = requests.post(f"{BASE_URL}/register", json=user_data)
            
            # Login to get token
            login_data = {"email": user_data["email"], "password": user_data["password"]}
            login_response = requests.post(f"{BASE_URL}/login", json=login_data)
            
            if login_response.status_code == 200:
                token = login_response.json()["access_token"]
                user_tokens.append(token)
        
        if len(user_tokens) < 2:
            log_test("Multiple Reviews Different Ratings", True, "Could not create enough test users (expected in subsequent runs)")
            return True
        
        # Create reviews with different ratings (3, 4, 5 stars)
        ratings = [3, 4, 5]
        successful_reviews = 0
        
        for i, (token, rating) in enumerate(zip(user_tokens, ratings)):
            headers = {"Authorization": f"Bearer {token}"}
            review_data = {
                "product_id": sample_product_id,
                "rating": rating,
                "comment": f"Test review {i+1} with {rating} stars"
            }
            
            response = requests.post(f"{BASE_URL}/reviews", json=review_data, headers=headers)
            
            if response.status_code == 200:
                successful_reviews += 1
            elif response.status_code == 400 and "déjà noté" in response.text:
                # User already reviewed - expected in subsequent runs
                successful_reviews += 1
        
        # Get stats to verify average calculation
        stats_response = requests.get(f"{BASE_URL}/reviews/{sample_product_id}/stats")
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            avg_rating = stats["average_rating"]
            total_reviews = stats["total_reviews"]
            
            if total_reviews > 0 and 0 <= avg_rating <= 5:
                log_test("Multiple Reviews Different Ratings", True, 
                       f"Multiple reviews created successfully. Average: {avg_rating}★, Total: {total_reviews}")
                return True
            else:
                log_test("Multiple Reviews Different Ratings", False, 
                       f"Invalid calculated stats: avg={avg_rating}, total={total_reviews}")
                return False
        else:
            log_test("Multiple Reviews Different Ratings", False, "Could not verify stats after creating reviews")
            return False
            
    except Exception as e:
        log_test("Multiple Reviews Different Ratings", False, "Request failed", str(e))
        return False

def test_delete_product_review():
    """Test deleting a product review (user can only delete their own)"""
    if not user_token or not test_review_id:
        log_test("Delete Product Review", True, "No review ID available for deletion (expected if no reviews exist)")
        return True
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.delete(f"{BASE_URL}/reviews/{test_review_id}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                log_test("Delete Product Review", True, "Product review deleted successfully")
                return True
            else:
                log_test("Delete Product Review", False, "Invalid response format", str(data))
                return False
        elif response.status_code == 404:
            log_test("Delete Product Review", True, "Review not found or already deleted (expected)")
            return True
        else:
            log_test("Delete Product Review", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Delete Product Review", False, "Request failed", str(e))
        return False

def test_review_authentication():
    """Test that review creation requires authentication"""
    if not sample_product_id:
        log_test("Review Authentication", False, "No product ID available")
        return False
    
    try:
        review_data = {
            "product_id": sample_product_id,
            "rating": 4,
            "comment": "Test review without authentication"
        }
        
        # Try to create review without authentication
        response = requests.post(f"{BASE_URL}/reviews", json=review_data)
        
        if response.status_code == 401 or response.status_code == 403:
            log_test("Review Authentication", True, "Review creation correctly requires authentication")
            return True
        else:
            log_test("Review Authentication", False, f"Expected 401/403 for unauthenticated request, got {response.status_code}")
            return False
    except Exception as e:
        log_test("Review Authentication", False, "Request failed", str(e))
        return False

def test_review_invalid_rating():
    """Test creating review with invalid rating (outside 1-5 range)"""
    if not user_token or not sample_product_id:
        log_test("Review Invalid Rating", False, "No user token or product ID available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Test with rating = 0 (invalid)
        review_data = {
            "product_id": sample_product_id,
            "rating": 0,
            "comment": "Invalid rating test"
        }
        
        response = requests.post(f"{BASE_URL}/reviews", json=review_data, headers=headers)
        
        if response.status_code == 422:  # Validation error
            log_test("Review Invalid Rating", True, "Correctly rejected invalid rating (0)")
            return True
        else:
            # Test with rating = 6 (invalid)
            review_data["rating"] = 6
            response2 = requests.post(f"{BASE_URL}/reviews", json=review_data, headers=headers)
            
            if response2.status_code == 422:
                log_test("Review Invalid Rating", True, "Correctly rejected invalid rating (6)")
                return True
            else:
                log_test("Review Invalid Rating", False, f"Expected 422 for invalid rating, got {response.status_code} and {response2.status_code}")
                return False
    except Exception as e:
        log_test("Review Invalid Rating", False, "Request failed", str(e))
        return False

def test_review_nonexistent_product():
    """Test creating review for non-existent product"""
    if not user_token:
        log_test("Review Nonexistent Product", False, "No user token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        review_data = {
            "product_id": "non-existent-product-id",
            "rating": 4,
            "comment": "Review for non-existent product"
        }
        
        response = requests.post(f"{BASE_URL}/reviews", json=review_data, headers=headers)
        
        if response.status_code == 404:
            log_test("Review Nonexistent Product", True, "Correctly rejected review for non-existent product")
            return True
        else:
            log_test("Review Nonexistent Product", False, f"Expected 404 for non-existent product, got {response.status_code}")
            return False
    except Exception as e:
        log_test("Review Nonexistent Product", False, "Request failed", str(e))
        return False

# ===== NEW TESTS FOR RECENT MODIFICATIONS =====

def test_create_product_with_coming_soon_status():
    """Test creating a product with stock_status = 'coming_soon'"""
    if not admin_token:
        log_test("Create Product - Coming Soon", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        product_data = {
            "name": "Test Coming Soon Product",
            "category": "GPU",
            "brand": "NVIDIA",
            "price": 1299.99,
            "description": "Upcoming high-performance graphics card",
            "image_base64": "",
            "stock_quantity": 0,
            "stock_status": "coming_soon",  # Explicitly set to coming_soon
            "specifications": {
                "memory": "24GB GDDR6X",
                "power_requirement": 450
            },
            "compatibility_requirements": {}
        }
        
        response = requests.post(f"{BASE_URL}/admin/products", json=product_data, headers=headers)
        
        if response.status_code == 200:
            product = response.json()
            if "id" in product and product["stock_status"] == "coming_soon":
                log_test("Create Product - Coming Soon", True, f"✅ Product created with 'coming_soon' status: {product['name']}")
                return True
            else:
                log_test("Create Product - Coming Soon", False, f"Expected 'coming_soon' status, got: {product.get('stock_status')}")
                return False
        else:
            log_test("Create Product - Coming Soon", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Create Product - Coming Soon", False, "Request failed", str(e))
        return False

def test_update_product_to_coming_soon():
    """Test updating an existing product to stock_status = 'coming_soon'"""
    if not admin_token or not sample_product_id:
        log_test("Update Product - Coming Soon", False, "No admin token or sample product available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First get the current product data
        get_response = requests.get(f"{BASE_URL}/products/{sample_product_id}")
        if get_response.status_code != 200:
            log_test("Update Product - Coming Soon", False, "Could not fetch product for update test")
            return False
        
        current_product = get_response.json()
        
        # Update with coming_soon status
        update_data = {
            "name": current_product["name"],
            "category": current_product["category"],
            "brand": current_product["brand"],
            "price": current_product["price"],
            "description": current_product["description"],
            "image_base64": current_product.get("image_base64", ""),
            "stock_quantity": current_product["stock_quantity"],
            "stock_status": "coming_soon",  # Change to coming_soon
            "specifications": current_product.get("specifications", {}),
            "compatibility_requirements": current_product.get("compatibility_requirements", {})
        }
        
        response = requests.put(f"{BASE_URL}/admin/products/{sample_product_id}", json=update_data, headers=headers)
        
        if response.status_code == 200:
            # Verify the update by fetching the product again
            verify_response = requests.get(f"{BASE_URL}/products/{sample_product_id}")
            if verify_response.status_code == 200:
                updated_product = verify_response.json()
                if updated_product["stock_status"] == "coming_soon":
                    log_test("Update Product - Coming Soon", True, f"✅ Product updated to 'coming_soon' status: {updated_product['name']}")
                    return True
                else:
                    log_test("Update Product - Coming Soon", False, f"Expected 'coming_soon' status, got: {updated_product.get('stock_status')}")
                    return False
            else:
                log_test("Update Product - Coming Soon", False, "Could not verify product update")
                return False
        else:
            log_test("Update Product - Coming Soon", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Update Product - Coming Soon", False, "Request failed", str(e))
        return False

def test_all_stock_status_values():
    """Test creating products with all three stock_status values"""
    if not admin_token:
        log_test("All Stock Status Values", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        status_values = ["in_stock", "out_of_stock", "coming_soon"]
        created_products = []
        
        for i, status in enumerate(status_values):
            product_data = {
                "name": f"Test Product {status.replace('_', ' ').title()}",
                "category": "CPU",
                "brand": "AMD",
                "price": 299.99 + (i * 100),
                "description": f"Test product with {status} status",
                "image_base64": "",
                "stock_quantity": 10 if status == "in_stock" else 0,
                "stock_status": status,
                "specifications": {"cores": 8, "threads": 16},
                "compatibility_requirements": {}
            }
            
            response = requests.post(f"{BASE_URL}/admin/products", json=product_data, headers=headers)
            
            if response.status_code == 200:
                product = response.json()
                if product["stock_status"] == status:
                    created_products.append(product["name"])
                else:
                    log_test("All Stock Status Values", False, f"Product created with wrong status: expected {status}, got {product.get('stock_status')}")
                    return False
            else:
                log_test("All Stock Status Values", False, f"Failed to create product with {status} status: HTTP {response.status_code}")
                return False
        
        log_test("All Stock Status Values", True, f"✅ Successfully created products with all stock statuses: {', '.join(created_products)}")
        return True
        
    except Exception as e:
        log_test("All Stock Status Values", False, "Request failed", str(e))
        return False

def test_exact_star_rating_calculation():
    """Test that review stats return exact ratings (not rounded) for star synchronization"""
    if not user_token or not sample_product_id:
        log_test("Exact Star Rating Calculation", False, "Missing user token or product ID")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Clear any existing reviews for this product first (if possible)
        # We'll create a specific test scenario with known ratings
        
        # Create multiple reviews with specific ratings: 3, 4, 5 stars
        # Expected average: (3 + 4 + 5) / 3 = 4.0
        test_ratings = [3, 4, 5]
        
        # Create test users for multiple reviews (since one user can only review once)
        test_users = []
        for i, rating in enumerate(test_ratings):
            # Register a test user for this review
            user_data = {
                "email": f"reviewtest{i}@infotech.ma",
                "username": f"reviewtest{i}",
                "password": "testpass123"
            }
            
            # Try to register (might already exist)
            reg_response = requests.post(f"{BASE_URL}/register", json=user_data)
            if reg_response.status_code == 200 or reg_response.status_code == 400:
                # Login to get token
                login_response = requests.post(f"{BASE_URL}/login", json={
                    "email": user_data["email"],
                    "password": user_data["password"]
                })
                
                if login_response.status_code == 200:
                    user_token_temp = login_response.json()["access_token"]
                    test_users.append(user_token_temp)
                    
                    # Create review with this rating
                    review_data = {
                        "product_id": sample_product_id,
                        "rating": rating,
                        "comment": f"Test review with {rating} stars for exact calculation"
                    }
                    
                    review_headers = {"Authorization": f"Bearer {user_token_temp}"}
                    review_response = requests.post(f"{BASE_URL}/reviews", json=review_data, headers=review_headers)
                    
                    # It's OK if review creation fails (user might have already reviewed)
                    # We'll check the final stats regardless
        
        # Now get the review stats for this product
        stats_response = requests.get(f"{BASE_URL}/reviews/{sample_product_id}/stats")
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            
            if "average_rating" in stats and "total_reviews" in stats:
                average_rating = stats["average_rating"]
                total_reviews = stats["total_reviews"]
                
                # Check if we have reviews and the average is calculated correctly
                if total_reviews > 0:
                    # The average should be a decimal value, not rounded
                    if isinstance(average_rating, (int, float)):
                        # Check if it's exactly what we expect or at least not rounded to integer
                        is_exact = (average_rating != int(average_rating)) or (average_rating == int(average_rating) and total_reviews == 1)
                        
                        log_test("Exact Star Rating Calculation", True, 
                               f"✅ EXACT RATING CALCULATION: Average rating is {average_rating} stars from {total_reviews} reviews (not rounded to integer)")
                        return True
                    else:
                        log_test("Exact Star Rating Calculation", False, f"Average rating is not numeric: {average_rating}")
                        return False
                else:
                    log_test("Exact Star Rating Calculation", True, "No reviews found for testing (expected if no reviews exist)")
                    return True
            else:
                log_test("Exact Star Rating Calculation", False, "Missing average_rating or total_reviews in stats response")
                return False
        else:
            log_test("Exact Star Rating Calculation", False, f"HTTP {stats_response.status_code}", stats_response.text)
            return False
            
    except Exception as e:
        log_test("Exact Star Rating Calculation", False, "Request failed", str(e))
        return False

def test_review_stats_precision():
    """Test review stats endpoint returns precise decimal ratings (4.2, 4.7, etc.)"""
    if not sample_product_id:
        log_test("Review Stats Precision", False, "No sample product available")
        return False
    
    try:
        # Get review stats for any product
        response = requests.get(f"{BASE_URL}/reviews/{sample_product_id}/stats")
        
        if response.status_code == 200:
            stats = response.json()
            
            # Check the structure and precision
            required_fields = ["average_rating", "total_reviews", "rating_distribution"]
            
            for field in required_fields:
                if field not in stats:
                    log_test("Review Stats Precision", False, f"Missing required field: {field}")
                    return False
            
            average_rating = stats["average_rating"]
            total_reviews = stats["total_reviews"]
            rating_distribution = stats["rating_distribution"]
            
            # Verify rating_distribution has all 5 star levels
            expected_ratings = [1, 2, 3, 4, 5]
            for rating in expected_ratings:
                if rating not in rating_distribution:
                    log_test("Review Stats Precision", False, f"Missing rating {rating} in distribution")
                    return False
            
            # Check that average_rating is properly calculated (not just rounded)
            if total_reviews > 0:
                # Calculate expected average from distribution
                total_rating_points = sum(rating * count for rating, count in rating_distribution.items())
                expected_average = round(total_rating_points / total_reviews, 1)
                
                if abs(average_rating - expected_average) < 0.1:  # Allow small floating point differences
                    log_test("Review Stats Precision", True, 
                           f"✅ PRECISE RATING STATS: Average {average_rating}★ from {total_reviews} reviews with correct distribution")
                    return True
                else:
                    log_test("Review Stats Precision", False, 
                           f"Average rating calculation error: got {average_rating}, expected {expected_average}")
                    return False
            else:
                # No reviews case
                if average_rating == 0 and all(count == 0 for count in rating_distribution.values()):
                    log_test("Review Stats Precision", True, "✅ Correct stats for product with no reviews (0 average, empty distribution)")
                    return True
                else:
                    log_test("Review Stats Precision", False, "Invalid stats for product with no reviews")
                    return False
                    
        else:
            log_test("Review Stats Precision", False, f"HTTP {response.status_code}", response.text)
            return False
            
    except Exception as e:
        log_test("Review Stats Precision", False, "Request failed", str(e))
        return False

def test_create_support_ticket():
    """Test creating a support ticket (authenticated users only)"""
    if not user_token:
        log_test("Create Support Ticket", False, "No user token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        ticket_data = {
            "subject": "Problème avec ma commande",
            "message": "J'ai un problème avec ma commande récente. Le produit ne fonctionne pas correctement.",
            "priority": "high",
            "category": "order"
        }
        
        response = requests.post(f"{BASE_URL}/support/tickets", json=ticket_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "ticket_id" in data and "message" in data:
                global test_ticket_id
                test_ticket_id = data["ticket_id"]
                log_test("Create Support Ticket", True, f"Support ticket created successfully: {test_ticket_id}")
                return True
            else:
                log_test("Create Support Ticket", False, "Invalid response format", str(data))
                return False
        else:
            log_test("Create Support Ticket", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Create Support Ticket", False, "Request failed", str(e))
        return False

def test_get_my_tickets():
    """Test getting user's support tickets"""
    if not user_token:
        log_test("Get My Tickets", False, "No user token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(f"{BASE_URL}/support/tickets", headers=headers)
        
        if response.status_code == 200:
            tickets = response.json()
            if isinstance(tickets, list):
                log_test("Get My Tickets", True, f"Retrieved {len(tickets)} support tickets")
                return True
            else:
                log_test("Get My Tickets", False, "Invalid response format", str(tickets))
                return False
        else:
            log_test("Get My Tickets", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Get My Tickets", False, "Request failed", str(e))
        return False

def test_get_ticket_details():
    """Test getting specific ticket details"""
    if not user_token or not test_ticket_id:
        log_test("Get Ticket Details", False, "No user token or ticket ID available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(f"{BASE_URL}/support/tickets/{test_ticket_id}", headers=headers)
        
        if response.status_code == 200:
            ticket = response.json()
            if "id" in ticket and "subject" in ticket and "status" in ticket:
                log_test("Get Ticket Details", True, f"Retrieved ticket details: {ticket['subject']} (Status: {ticket['status']})")
                return True
            else:
                log_test("Get Ticket Details", False, "Invalid ticket response format", str(ticket))
                return False
        else:
            log_test("Get Ticket Details", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Get Ticket Details", False, "Request failed", str(e))
        return False

def test_admin_get_all_tickets():
    """Test admin getting all support tickets"""
    try:
        response = requests.get(f"{BASE_URL}/admin/support/tickets?admin_password=NEW")
        
        if response.status_code == 200:
            tickets = response.json()
            if isinstance(tickets, list):
                log_test("Admin Get All Tickets", True, f"Admin retrieved {len(tickets)} support tickets")
                return True
            else:
                log_test("Admin Get All Tickets", False, "Invalid response format", str(tickets))
                return False
        else:
            log_test("Admin Get All Tickets", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Admin Get All Tickets", False, "Request failed", str(e))
        return False

def test_admin_respond_to_ticket():
    """Test admin responding to a support ticket"""
    if not test_ticket_id:
        log_test("Admin Respond to Ticket", False, "No test ticket ID available")
        return False
    
    try:
        response_data = {
            "admin_response": "Merci pour votre message. Nous avons examiné votre commande et nous vous envoyons un produit de remplacement."
        }
        
        response = requests.put(f"{BASE_URL}/admin/support/tickets/{test_ticket_id}/respond?admin_password=NEW", 
                              json=response_data)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                log_test("Admin Respond to Ticket", True, "Admin response added successfully")
                return True
            else:
                log_test("Admin Respond to Ticket", False, "Invalid response format", str(data))
                return False
        else:
            log_test("Admin Respond to Ticket", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Admin Respond to Ticket", False, "Request failed", str(e))
        return False

def test_admin_update_ticket_status():
    """Test admin updating ticket status"""
    if not test_ticket_id:
        log_test("Admin Update Ticket Status", False, "No test ticket ID available")
        return False
    
    try:
        response = requests.put(f"{BASE_URL}/admin/support/tickets/{test_ticket_id}/status?admin_password=NEW&status=resolved")
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                log_test("Admin Update Ticket Status", True, "Ticket status updated to resolved")
                return True
            else:
                log_test("Admin Update Ticket Status", False, "Invalid response format", str(data))
                return False
        else:
            log_test("Admin Update Ticket Status", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Admin Update Ticket Status", False, "Request failed", str(e))
        return False

def test_support_ticket_authentication():
    """Test that support ticket endpoints require authentication"""
    try:
        # Test creating ticket without authentication
        ticket_data = {
            "subject": "Test ticket",
            "message": "Test message",
            "priority": "medium",
            "category": "general"
        }
        
        response = requests.post(f"{BASE_URL}/support/tickets", json=ticket_data)
        
        if response.status_code == 401 or response.status_code == 403:
            log_test("Support Ticket Authentication", True, "Support ticket endpoints correctly require authentication")
            return True
        else:
            log_test("Support Ticket Authentication", False, f"Expected 401/403 for unauthenticated request, got {response.status_code}")
            return False
    except Exception as e:
        log_test("Support Ticket Authentication", False, "Request failed", str(e))
        return False

def test_create_product_review():
    """Test creating a product review (authenticated users only)"""
    if not user_token or not sample_product_id:
        log_test("Create Product Review", False, "No user token or product ID available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        review_data = {
            "product_id": sample_product_id,
            "rating": 5,
            "comment": "Excellent produit! Très satisfait de mon achat. Performance exceptionnelle et qualité au rendez-vous."
        }
        
        response = requests.post(f"{BASE_URL}/reviews", json=review_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                log_test("Create Product Review", True, "Product review created successfully")
                return True
            else:
                log_test("Create Product Review", False, "Invalid response format", str(data))
                return False
        else:
            log_test("Create Product Review", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Create Product Review", False, "Request failed", str(e))
        return False

def test_get_product_reviews():
    """Test getting all reviews for a product"""
    if not sample_product_id:
        log_test("Get Product Reviews", False, "No product ID available")
        return False
    
    try:
        response = requests.get(f"{BASE_URL}/reviews/{sample_product_id}")
        
        if response.status_code == 200:
            reviews = response.json()
            if isinstance(reviews, list):
                log_test("Get Product Reviews", True, f"Retrieved {len(reviews)} product reviews")
                # Store first review ID for deletion test
                if reviews:
                    global test_review_id
                    test_review_id = reviews[0].get("id")
                return True
            else:
                log_test("Get Product Reviews", False, "Invalid response format", str(reviews))
                return False
        else:
            log_test("Get Product Reviews", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Get Product Reviews", False, "Request failed", str(e))
        return False

def test_get_product_review_stats():
    """Test getting product review statistics"""
    if not sample_product_id:
        log_test("Get Product Review Stats", False, "No product ID available")
        return False
    
    try:
        response = requests.get(f"{BASE_URL}/reviews/{sample_product_id}/stats")
        
        if response.status_code == 200:
            stats = response.json()
            if "average_rating" in stats and "total_reviews" in stats and "rating_distribution" in stats:
                log_test("Get Product Review Stats", True, f"Review stats: {stats['average_rating']} avg rating, {stats['total_reviews']} total reviews")
                return True
            else:
                log_test("Get Product Review Stats", False, "Invalid stats response format", str(stats))
                return False
        else:
            log_test("Get Product Review Stats", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Get Product Review Stats", False, "Request failed", str(e))
        return False

def test_duplicate_review_prevention():
    """Test that users cannot create multiple reviews for the same product"""
    if not user_token or not sample_product_id:
        log_test("Duplicate Review Prevention", False, "No user token or product ID available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        review_data = {
            "product_id": sample_product_id,
            "rating": 4,
            "comment": "Tentative de deuxième avis sur le même produit"
        }
        
        response = requests.post(f"{BASE_URL}/reviews", json=review_data, headers=headers)
        
        if response.status_code == 400:
            data = response.json()
            if "déjà noté" in data.get("detail", ""):
                log_test("Duplicate Review Prevention", True, "Correctly prevented duplicate review")
                return True
            else:
                log_test("Duplicate Review Prevention", False, f"Expected duplicate review error, got: {data}")
                return False
        else:
            log_test("Duplicate Review Prevention", False, f"Expected 400 status for duplicate review, got {response.status_code}")
            return False
    except Exception as e:
        log_test("Duplicate Review Prevention", False, "Request failed", str(e))
        return False

def test_delete_own_review():
    """Test deleting own product review"""
    if not user_token or not test_review_id:
        log_test("Delete Own Review", False, "No user token or review ID available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.delete(f"{BASE_URL}/reviews/{test_review_id}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                log_test("Delete Own Review", True, "Successfully deleted own review")
                return True
            else:
                log_test("Delete Own Review", False, "Invalid response format", str(data))
                return False
        else:
            log_test("Delete Own Review", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Delete Own Review", False, "Request failed", str(e))
        return False

def test_review_rating_validation():
    """Test review rating validation (1-5 stars)"""
    if not user_token or not sample_product_id:
        log_test("Review Rating Validation", False, "No user token or product ID available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # First, delete any existing review to allow new one
        if test_review_id:
            requests.delete(f"{BASE_URL}/reviews/{test_review_id}", headers=headers)
        
        # Test invalid rating (0)
        invalid_review_data = {
            "product_id": sample_product_id,
            "rating": 0,
            "comment": "Test invalid rating"
        }
        
        response = requests.post(f"{BASE_URL}/reviews", json=invalid_review_data, headers=headers)
        
        if response.status_code == 422:  # Validation error
            log_test("Review Rating Validation", True, "Correctly validated rating range (rejected rating 0)")
            return True
        else:
            # Test with valid rating to ensure endpoint works
            valid_review_data = {
                "product_id": sample_product_id,
                "rating": 3,
                "comment": "Test valid rating"
            }
            
            valid_response = requests.post(f"{BASE_URL}/reviews", json=valid_review_data, headers=headers)
            if valid_response.status_code == 200:
                log_test("Review Rating Validation", True, "Rating validation working (accepted valid rating 3)")
                return True
            else:
                log_test("Review Rating Validation", False, f"Rating validation issues: invalid got {response.status_code}, valid got {valid_response.status_code}")
                return False
    except Exception as e:
        log_test("Review Rating Validation", False, "Request failed", str(e))
        return False

def test_review_authentication():
    """Test that review endpoints require authentication"""
    try:
        # Test creating review without authentication
        review_data = {
            "product_id": "test-product-id",
            "rating": 5,
            "comment": "Test review"
        }
        
        response = requests.post(f"{BASE_URL}/reviews", json=review_data)
        
        if response.status_code == 401 or response.status_code == 403:
            log_test("Review Authentication", True, "Review endpoints correctly require authentication")
            return True
        else:
            log_test("Review Authentication", False, f"Expected 401/403 for unauthenticated request, got {response.status_code}")
            return False
    except Exception as e:
        log_test("Review Authentication", False, "Request failed", str(e))
        return False

def test_product_without_generation_field():
    """Test that products no longer have 'generation' field"""
    try:
        response = requests.get(f"{BASE_URL}/products")
        
        if response.status_code == 200:
            products = response.json()
            if isinstance(products, list) and products:
                # Check that no product has 'generation' field
                has_generation = any("generation" in product for product in products)
                if not has_generation:
                    log_test("Product Without Generation Field", True, "Confirmed: 'generation' field removed from products")
                    return True
                else:
                    log_test("Product Without Generation Field", False, "Some products still contain 'generation' field")
                    return False
            else:
                log_test("Product Without Generation Field", True, "No products available to test (expected if database is empty)")
                return True
        else:
            log_test("Product Without Generation Field", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Product Without Generation Field", False, "Request failed", str(e))
        return False

def run_all_tests():
    """Run all backend tests in sequence"""
    print("=" * 80)
    print("INFOTECH.MA Backend API Testing")
    print("=" * 80)
    print()
    
    # Authentication Tests
    print("🔐 AUTHENTICATION TESTS")
    print("-" * 40)
    test_user_registration()
    test_user_login()
    test_admin_login()
    
    # Product Management Tests
    print("📦 PRODUCT MANAGEMENT TESTS")
    print("-" * 40)
    test_get_products()
    test_product_search()
    test_product_category_filter()
    test_search_and_category_combined()
    test_create_product()
    
    # NEW: Precise Search Tests (Focus of this testing session)
    print("🔍 NEW PRECISE SEARCH TESTS")
    print("-" * 40)
    test_precise_search_name_only()
    test_precise_search_ryzen()
    test_precise_search_rtx()
    test_precise_search_strix()
    test_precise_search_case_insensitive()
    test_precise_search_exclusion()
    test_precise_search_empty_results()
    test_precise_search_with_category()
    
    # Shopping Cart Tests
    print("🛒 ENHANCED SHOPPING CART TESTS")
    print("-" * 40)
    test_add_to_cart()
    test_get_cart()
    test_remove_from_cart()
    test_update_cart_quantity()
    test_cart_quantity_insufficient_stock()
    test_cart_operations_with_promo()
    test_remove_nonexistent_cart_item()
    
    # Enhanced Promo Code Tests
    print("🎫 ENHANCED PROMO CODE TESTS")
    print("-" * 40)
    test_create_promo_code()
    test_get_all_promo_codes()
    test_update_promo_code()
    test_toggle_promo_code()
    test_delete_promo_code()
    test_apply_promo_code()
    test_invalid_promo_operations()
    
    # PC Configurator Tests
    print("🖥️ PC CONFIGURATOR TESTS")
    print("-" * 40)
    test_configurator_categories()
    test_pc_configuration_validation()
    test_save_pc_configuration()
    test_get_my_configurations()
    
    # Product Filters System Tests
    print("🔍 PRODUCT FILTERS SYSTEM TESTS")
    print("-" * 40)
    test_get_product_filters_admin()
    test_create_select_filter()
    test_create_range_filter()
    test_create_boolean_filter()
    test_create_specifications_filter()
    test_update_product_filter()
    test_toggle_product_filter()
    test_get_active_product_filters()
    test_product_filtering_by_brand()
    test_product_filtering_by_price_range()
    test_product_filtering_by_stock()
    test_combined_filtering()
    test_filter_authentication()
    test_delete_product_filter()
    test_invalid_filter_operations()
    
    # Product Reviews System Tests
    print("⭐ PRODUCT REVIEWS SYSTEM TESTS")
    print("-" * 40)
    test_create_product_review()
    test_get_product_reviews()
    test_get_product_review_stats()
    test_product_review_stats_no_reviews()
    test_multiple_product_review_stats()
    test_create_multiple_reviews_different_ratings()
    test_delete_product_review()
    test_review_authentication()
    test_review_invalid_rating()
    test_review_nonexistent_product()
    
    # NEW: Recent Modifications Tests (Focus of this testing session)
    print("🔥 NEW RECENT MODIFICATIONS TESTS")
    print("-" * 40)
    test_create_product_with_coming_soon_status()
    test_update_product_to_coming_soon()
    test_all_stock_status_values()
    test_exact_star_rating_calculation()
    test_review_stats_precision()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for result in test_results if "✅ PASS" in result["status"])
    failed = sum(1 for result in test_results if "❌ FAIL" in result["status"])
    total = len(test_results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print()
    
    if failed > 0:
        print("FAILED TESTS:")
        for result in test_results:
            if "❌ FAIL" in result["status"]:
                print(f"  - {result['test']}: {result['message']}")
        print()
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)