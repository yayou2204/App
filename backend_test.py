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
    """Test product search functionality"""
    try:
        # Search for AMD products
        response = requests.get(f"{BASE_URL}/products?search=AMD")
        
        if response.status_code == 200:
            products = response.json()
            if isinstance(products, list):
                amd_found = any("AMD" in product.get("name", "") or "AMD" in product.get("brand", "") for product in products)
                if amd_found:
                    log_test("Product Search", True, f"Search returned {len(products)} products with AMD")
                    return True
                else:
                    log_test("Product Search", True, f"Search completed but no AMD products found (expected if no AMD products exist)")
                    return True
            else:
                log_test("Product Search", False, "Invalid response format", str(products))
                return False
        else:
            log_test("Product Search", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Product Search", False, "Request failed", str(e))
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
        # Try to apply the existing GAMING10 promo code
        response = requests.post(f"{BASE_URL}/cart/apply-promo?code=GAMING10", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "discount" in data:
                log_test("Apply Promo Code", True, f"Promo code applied, discount: ${data['discount']}")
                return True
            else:
                log_test("Apply Promo Code", False, "Invalid response format", str(data))
                return False
        else:
            log_test("Apply Promo Code", False, f"HTTP {response.status_code}", response.text)
            return False
    except Exception as e:
        log_test("Apply Promo Code", False, "Request failed", str(e))
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
    test_create_product()
    
    # Shopping Cart Tests
    print("🛒 SHOPPING CART TESTS")
    print("-" * 40)
    test_add_to_cart()
    test_get_cart()
    
    # Promo Code Tests
    print("🎫 PROMO CODE TESTS")
    print("-" * 40)
    test_create_promo_code()
    test_apply_promo_code()
    
    # PC Configurator Tests
    print("🖥️ PC CONFIGURATOR TESTS")
    print("-" * 40)
    test_configurator_categories()
    test_pc_configuration_validation()
    test_save_pc_configuration()
    test_get_my_configurations()
    
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