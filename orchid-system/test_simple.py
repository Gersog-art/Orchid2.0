#!/usr/bin/env python3
import requests
import time

def test_endpoint(url, name):
    try:
        print(f"\nTesting {name} at {url}")
        
        # Test health endpoint
        health_url = f"{url}/health"
        response = requests.get(health_url, timeout=3)
        print(f"  Health: {response.status_code} - {response.json()}")
        
        # Test prediction endpoint
        predict_url = f"{url}/predict"
        test_data = {"features": [1, 2, 3, 4, 5]}
        response = requests.post(predict_url, json=test_data, timeout=3)
        print(f"  Predict: {response.status_code} - {response.json()}")
        
        return True
    except requests.exceptions.ConnectionError:
        print(f"  ✗ Cannot connect to {url}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    endpoints = [
        ("http://localhost:8001", "Isolation Forest"),
        ("http://localhost:8002", "Random Forest")
    ]
    
    print("=" * 50)
    print("Testing Orchid ML Services")
    print("=" * 50)
    
    results = []
    for url, name in endpoints:
        success = test_endpoint(url, name)
        results.append((name, success))
        time.sleep(1)
    
    print("\n" + "=" * 50)
    print("Summary:")
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {name}")
    
    if all([r[1] for r in results]):
        print("\nAll services are working correctly!")
        print("You can now access the admin panel at: http://localhost:3000")
    else:
        print("\nSome services failed. Check logs with: docker-compose logs")

if __name__ == "__main__":
    main()
