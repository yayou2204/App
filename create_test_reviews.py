#!/usr/bin/env python3
"""
Create comprehensive test reviews for all products to test the star system
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
print(f"Creating comprehensive test reviews at: {BASE_URL}")
print("=" * 80)

def create_comprehensive_test_reviews():
    """Create test reviews for multiple products with different ratings"""
    
    # Login as test user
    login_response = requests.post(f"{BASE_URL}/login", json={
        "email": "testuser@infotech.ma",
        "password": "testpass123"
    })
    
    if login_response.status_code != 200:
        print("❌ Failed to login")
        return False
    
    user_token = login_response.json()['access_token']
    headers = {"Authorization": f"Bearer {user_token}"}
    print("✅ Logged in successfully")
    
    # Get all products
    products_response = requests.get(f"{BASE_URL}/products")
    if products_response.status_code != 200:
        print("❌ Failed to get products")
        return False
    
    products = products_response.json()
    print(f"✅ Found {len(products)} products")
    
    # Create reviews for the main products (first 4)
    test_reviews = [
        {"rating": 5, "comment": "Excellent CPU! Perfect for gaming and streaming."},
        {"rating": 4, "comment": "Great motherboard, solid build quality."},
        {"rating": 3, "comment": "Good GPU but a bit pricey."},
        {"rating": 5, "comment": "Amazing performance, highly recommended!"}
    ]
    
    for i, product in enumerate(products[:4]):
        product_id = product['id']
        product_name = product['name']
        
        if i < len(test_reviews):
            review_data = {
                "product_id": product_id,
                "rating": test_reviews[i]["rating"],
                "comment": test_reviews[i]["comment"]
            }
            
            print(f"\n--- Creating review for: {product_name} ---")
            print(f"Rating: {review_data['rating']}★")
            print(f"Comment: {review_data['comment']}")
            
            review_response = requests.post(f"{BASE_URL}/reviews", json=review_data, headers=headers)
            
            if review_response.status_code == 200:
                print(f"✅ Review created successfully")
            elif review_response.status_code == 400 and "déjà noté" in review_response.text:
                print(f"✅ Review already exists (expected)")
            else:
                print(f"❌ Failed to create review: {review_response.status_code}")
                print(f"   Response: {review_response.text}")
    
    # Now check all product stats
    print(f"\n" + "=" * 80)
    print("📊 FINAL REVIEW STATS FOR ALL PRODUCTS")
    print("=" * 80)
    
    for product in products:
        product_id = product['id']
        product_name = product['name']
        
        stats_response = requests.get(f"{BASE_URL}/reviews/{product_id}/stats")
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            avg_rating = stats.get('average_rating', 0)
            total_reviews = stats.get('total_reviews', 0)
            
            if total_reviews > 0:
                print(f"🌟 {product_name}: {avg_rating}★ ({total_reviews} reviews)")
            else:
                print(f"⚪ {product_name}: No reviews")
        else:
            print(f"❌ {product_name}: Stats failed")
    
    print(f"\n" + "=" * 80)
    print("✅ TEST REVIEW CREATION COMPLETE")
    print("The products with stars should now display properly on the frontend!")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    create_comprehensive_test_reviews()