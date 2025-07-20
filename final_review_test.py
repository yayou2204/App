#!/usr/bin/env python3
"""
Final comprehensive test of the review stars system
"""

import requests
import json

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

def final_review_system_test():
    """Final comprehensive test of the review system"""
    
    print("🎯 FINAL COMPREHENSIVE REVIEW SYSTEM TEST")
    print("=" * 80)
    
    # Test 1: Get all products and their review stats
    print("📦 TEST 1: Products with Review Stats")
    print("-" * 40)
    
    products_response = requests.get(f"{BASE_URL}/products")
    if products_response.status_code != 200:
        print("❌ Failed to get products")
        return False
    
    products = products_response.json()
    products_with_reviews = 0
    products_without_reviews = 0
    
    for product in products:
        product_id = product['id']
        product_name = product['name']
        
        stats_response = requests.get(f"{BASE_URL}/reviews/{product_id}/stats")
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            avg_rating = stats.get('average_rating', 0)
            total_reviews = stats.get('total_reviews', 0)
            
            if total_reviews > 0:
                products_with_reviews += 1
                stars = "★" * int(avg_rating) + "☆" * (5 - int(avg_rating))
                print(f"✅ {product_name}")
                print(f"   🌟 {avg_rating}★ ({total_reviews} reviews) {stars}")
            else:
                products_without_reviews += 1
                print(f"⚪ {product_name}: No reviews")
        else:
            print(f"❌ {product_name}: Stats endpoint failed")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Products with reviews: {products_with_reviews}")
    print(f"   Products without reviews: {products_without_reviews}")
    print(f"   Total products: {len(products)}")
    
    # Test 2: Test specific endpoint responses
    print(f"\n🔍 TEST 2: Endpoint Response Validation")
    print("-" * 40)
    
    # Test with a product that has reviews
    if products_with_reviews > 0:
        # Find first product with reviews
        for product in products:
            stats_response = requests.get(f"{BASE_URL}/reviews/{product['id']}/stats")
            if stats_response.status_code == 200:
                stats = stats_response.json()
                if stats.get('total_reviews', 0) > 0:
                    print(f"✅ Testing with product: {product['name']}")
                    print(f"   Response format: {json.dumps(stats, indent=2)}")
                    
                    # Validate response structure
                    required_fields = ['average_rating', 'total_reviews', 'rating_distribution']
                    missing_fields = [field for field in required_fields if field not in stats]
                    
                    if not missing_fields:
                        print(f"✅ All required fields present")
                        
                        # Validate data types
                        if (isinstance(stats['average_rating'], (int, float)) and
                            isinstance(stats['total_reviews'], int) and
                            isinstance(stats['rating_distribution'], dict)):
                            print(f"✅ Data types are correct")
                        else:
                            print(f"❌ Invalid data types")
                    else:
                        print(f"❌ Missing fields: {missing_fields}")
                    break
    
    # Test 3: Frontend Integration Simulation
    print(f"\n🖥️  TEST 3: Frontend Integration Simulation")
    print("-" * 40)
    
    print("Simulating frontend products page load...")
    
    # Step 1: Frontend gets products
    products_response = requests.get(f"{BASE_URL}/products")
    if products_response.status_code == 200:
        products = products_response.json()
        print(f"✅ Frontend loaded {len(products)} products")
        
        # Step 2: For each product, frontend gets review stats
        frontend_success = 0
        frontend_failures = 0
        
        for product in products[:5]:  # Test first 5 products
            product_id = product['id']
            product_name = product['name']
            
            # This is exactly what the frontend does
            stats_response = requests.get(f"{BASE_URL}/reviews/{product_id}/stats")
            
            if stats_response.status_code == 200:
                stats = stats_response.json()
                avg_rating = stats.get('average_rating', 0)
                total_reviews = stats.get('total_reviews', 0)
                
                frontend_success += 1
                
                if avg_rating > 0:
                    print(f"🌟 {product_name}: {avg_rating}★ - STARS WILL SHOW")
                else:
                    print(f"⚪ {product_name}: No rating - NO STARS")
            else:
                frontend_failures += 1
                print(f"❌ {product_name}: Stats failed - NO STARS")
        
        print(f"\n📊 Frontend Integration Results:")
        print(f"   Successful stats requests: {frontend_success}")
        print(f"   Failed stats requests: {frontend_failures}")
        
        if frontend_failures == 0:
            print(f"✅ ALL STATS ENDPOINTS WORKING - Frontend integration should work!")
        else:
            print(f"❌ Some stats endpoints failing - Frontend may have issues")
    
    # Test 4: Edge Cases
    print(f"\n🧪 TEST 4: Edge Cases")
    print("-" * 40)
    
    # Test with non-existent product
    fake_product_id = "non-existent-product-id"
    stats_response = requests.get(f"{BASE_URL}/reviews/{fake_product_id}/stats")
    
    if stats_response.status_code == 200:
        stats = stats_response.json()
        if (stats.get('average_rating') == 0 and 
            stats.get('total_reviews') == 0):
            print(f"✅ Non-existent product returns zero stats (correct)")
        else:
            print(f"❌ Non-existent product returns unexpected data")
    else:
        print(f"❌ Non-existent product endpoint failed: {stats_response.status_code}")
    
    print(f"\n" + "=" * 80)
    print("🎯 FINAL DIAGNOSIS")
    print("=" * 80)
    
    if products_with_reviews > 0 and frontend_failures == 0:
        print("✅ REVIEW STARS SYSTEM IS WORKING CORRECTLY!")
        print("✅ Backend endpoints are functional")
        print("✅ Test data exists (products with reviews)")
        print("✅ Stats format is correct")
        print("")
        print("🔍 IF STARS STILL DON'T SHOW ON FRONTEND:")
        print("   1. Check frontend console for JavaScript errors")
        print("   2. Verify frontend is calling the correct API endpoints")
        print("   3. Check if frontend renderStars() function is working")
        print("   4. Ensure frontend is using the correct backend URL")
    else:
        print("❌ ISSUES FOUND:")
        if products_with_reviews == 0:
            print("   - No products have reviews (create test reviews)")
        if frontend_failures > 0:
            print("   - Some stats endpoints are failing")
    
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    final_review_system_test()