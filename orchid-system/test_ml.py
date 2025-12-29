#!/usr/bin/env python3
import requests
import time

def test_service(port, name):
    url = f"http://localhost:{port}"
    print(f"\nТестируем {name} на порту {port}...")
    
    try:
        # Проверяем health
        health_url = f"{url}/health"
        response = requests.get(health_url, timeout=3)
        print(f"  Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"  Ответ: {response.json()}")
        
        # Проверяем predict
        predict_url = f"{url}/predict"
        test_data = {"test": "attack"}
        response = requests.post(predict_url, json=test_data, timeout=3)
        print(f"  Predict: {response.status_code}")
        if response.status_code == 200:
            print(f"  Ответ: {response.json()}")
        
        return True
    except Exception as e:
        print(f"  Ошибка: {e}")
        return False

def main():
    print("=" * 50)
    print("Тестирование системы Orchid")
    print("=" * 50)
    
    services = [
        (8001, "Isolation Forest"),
        (8002, "Random Forest")
    ]
    
    results = []
    for port, name in services:
        success = test_service(port, name)
        results.append((name, success))
        time.sleep(1)
    
    print("\n" + "=" * 50)
    print("Результаты:")
    for name, success in results:
        status = "✓ РАБОТАЕТ" if success else "✗ НЕ РАБОТАЕТ"
        print(f"{status} - {name}")

if __name__ == "__main__":
    main()
