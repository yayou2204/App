#!/usr/bin/env python3
"""
Focused test for review stars system - specifically testing why stars don't show on products page
"""

import requests
import json
import sys

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
print(f"Testing review stars system at: {BASE_URL}")
print("=" * 80)

def test_review_stars_system():
    """Test the complete review stars system for products page"""
    
    # Step 1: Get all products
    print("🔍 STEP 1: Getting all products...")
    products_response = requests.get(f"{BASE_URL}/products")
    
    if products_response.status_code != 200:
        print(f"❌ Failed to get products: {products_response.status_code}")
        return False
    
    products = products_response.json()
    print(f"✅ Found {len(products)} products")
    
    # Step 2: Check review stats for each product
    print("\n⭐ STEP 2: Checking review stats for each product...")
    
    for i, product in enumerate(products, 1):
        product_id = product['id']
        product_name = product['name']
        
        print(f"\n--- Product {i}: {product_name} ---")
        print(f"Product ID: {product_id}")
        
        # Get review stats
        stats_response = requests.get(f"{BASE_URL}/reviews/{product_id}/stats")
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            avg_rating = stats.get('average_rating', 0)
            total_reviews = stats.get('total_reviews', 0)
            rating_dist = stats.get('rating_distribution', {})
            
            print(f"✅ Stats endpoint working")
            print(f"   Average Rating: {avg_rating}★")
            print(f"   Total Reviews: {total_reviews}")
            print(f"   Rating Distribution: {rating_dist}")
            
            if total_reviews == 0:
                print("⚠️  NO REVIEWS FOUND - This explains why no stars show!")
            else:
                print(f"✅ Has {total_reviews} reviews with {avg_rating}★ average")
                
        else:
            print(f"❌ Stats endpoint failed: {stats_response.status_code}")
            print(f"   Response: {stats_response.text}")
    
    # Step 3: Check if we need to create test reviews
    print(f"\n🎯 STEP 3: Creating test reviews for sample products...")
    
    # First, let's login to get a user token
    print("Logging in as test user...")
    login_response = requests.post(f"{BASE_URL}/login", json={
        "email": "testuser@infotech.ma",
        "password": "testpass123"
    })
    
    if login_response.status_code != 200:
        print("❌ Failed to login - cannot create test reviews")
        return False
    
    user_token = login_response.json()['access_token']
    headers = {"Authorization": f"Bearer {user_token}"}
    print("✅ Logged in successfully")
    
    # Create test reviews for the first two products (AMD Ryzen and ASUS motherboard)
    sample_products = products[:2]  # Take first 2 products
    
    for product in sample_products:
        product_id = product['id']
        product_name = product['name']
        
        print(f"\n--- Creating test review for: {product_name} ---")
        
        # Check if review already exists
        existing_reviews = requests.get(f"{BASE_URL}/reviews/{product_id}")
        if existing_reviews.status_code == 200:
            reviews = existing_reviews.json()
            if len(reviews) > 0:
                print(f"✅ Product already has {len(reviews)} reviews")
                continue
        
        # Create a test review
        review_data = {
            "product_id": product_id,
            "rating": 4,  # 4 stars
            "comment": f"Great product! Test review for {product_name}"
        }
        
        review_response = requests.post(f"{BASE_URL}/reviews", json=review_data, headers=headers)
        
        if review_response.status_code == 200:
            print(f"✅ Created test review (4★) for {product_name}")
        elif review_response.status_code == 400 and "déjà noté" in review_response.text:
            print(f"✅ Review already exists for {product_name}")
        else:
            print(f"❌ Failed to create review: {review_response.status_code}")
            print(f"   Response: {review_response.text}")
    
    # Step 4: Re-check stats after creating reviews
    print(f"\n🔄 STEP 4: Re-checking stats after creating test reviews...")
    
    for product in sample_products:
        product_id = product['id']
        product_name = product['name']
        
        print(f"\n--- Updated stats for: {product_name} ---")
        
        stats_response = requests.get(f"{BASE_URL}/reviews/{product_id}/stats")
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            avg_rating = stats.get('average_rating', 0)
            total_reviews = stats.get('total_reviews', 0)
            
            print(f"✅ Average Rating: {avg_rating}★")
            print(f"✅ Total Reviews: {total_reviews}")
            
            if total_reviews > 0:
                print(f"🌟 STARS SHOULD NOW APPEAR ON FRONTEND!")
            else:
                print(f"⚠️  Still no reviews - stars won't appear")
        else:
            print(f"❌ Stats check failed: {stats_response.status_code}")
    
    # Step 5: Test the exact endpoint the frontend uses
    print(f"\n🎯 STEP 5: Testing exact frontend integration...")
    
    # Simulate what the frontend does - get products and their stats
    print("Simulating frontend products page load...")
    
    products_response = requests.get(f"{BASE_URL}/products")
    if products_response.status_code == 200:
        products = products_response.json()
        print(f"✅ Products loaded: {len(products)} products")
        
        # For each product, get stats (like frontend does)
        for product in products[:3]:  # Test first 3 products
            product_id = product['id']
            product_name = product['name']
            
            stats_response = requests.get(f"{BASE_URL}/reviews/{product_id}/stats")
            if stats_response.status_code == 200:
                stats = stats_response.json()
                avg_rating = stats.get('average_rating', 0)
                total_reviews = stats.get('total_reviews', 0)
                
                print(f"📦 {product_name}")
                print(f"   🌟 {avg_rating}★ ({total_reviews} reviews)")
                
                if avg_rating > 0:
                    print(f"   ✅ FRONTEND SHOULD SHOW {avg_rating} STARS")
                else:
                    print(f"   ⚠️  NO STARS (no reviews)")
            else:
                print(f"   ❌ Stats failed for {product_name}")
    
    print(f"\n" + "=" * 80)
    print("🎯 DIAGNOSIS COMPLETE")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    test_review_stars_system()