#!/usr/bin/env python3
"""
Simple agent to monitor Juice Shop traffic and send to Orchid
"""
import requests
import json
import time
import random
from datetime import datetime

class JuiceShopMonitor:
    def __init__(self):
        self.juice_shop_url = "http://localhost:3001"
        self.ml_isolation_url = "http://localhost:8001/predict"
        self.ml_random_url = "http://localhost:8002/predict"
        self.running = True
        
    def generate_simulated_traffic(self):
        """Генерируем симулированный трафик атак"""
        endpoints = [
            "/rest/user/login",
            "/api/Products",
            "/profile",
            "/#/search",
            "/rest/basket",
            "/rest/admin/application-configuration"
        ]
        
        attacks = [
            {"type": "sqli", "payload": "' UNION SELECT username, password FROM Users--"},
            {"type": "xss", "payload": "<img src=x onerror=alert(1)>"},
            {"type": "lfi", "payload": "../../../../etc/passwd"},
            {"type": "rce", "payload": "; cat /etc/shadow"},
            {"type": "xxe", "payload": "<!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>"},
        ]
        
        normal_requests = [
            {"type": "normal", "payload": "product=1"},
            {"type": "normal", "payload": "search=apple"},
            {"type": "normal", "payload": "email=user@test.com"},
            {"type": "normal", "payload": "page=1"},
        ]
        
        # 30% chance of attack
        if random.random() < 0.3:
            return random.choice(endpoints), random.choice(attacks)
        else:
            return random.choice(endpoints), random.choice(normal_requests)
    
    def send_to_ml(self, endpoint, attack_data):
        """Отправляем данные в ML сервисы"""
        ml_data = {
            "request": {
                "url": f"{self.juice_shop_url}{endpoint}",
                "method": "POST" if "login" in endpoint else "GET",
                "body": attack_data["payload"],
                "headers": {
                    "User-Agent": f"Mozilla/5.0 ({attack_data['type']} Test)",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            },
            "metadata": {
                "source_ip": f"192.168.1.{random.randint(1, 255)}",
                "timestamp": datetime.now().isoformat(),
                "attack_type": attack_data["type"]
            }
        }
        
        try:
            # Отправляем в Isolation Forest
            iso_response = requests.post(
                self.ml_isolation_url,
                json=ml_data,
                timeout=1
            )
            
            # Отправляем в Random Forest
            rf_response = requests.post(
                self.ml_random_url,
                json=ml_data,
                timeout=1
            )
            
            if iso_response.status_code == 200 and rf_response.status_code == 200:
                iso_result = iso_response.json()
                rf_result = rf_response.json()
                
                # Логируем атаку если обнаружена
                if iso_result.get("is_anomaly", False) or rf_result.get("is_attack", False):
                    print(f"[!] Атака обнаружена: {attack_data['type']}")
                    print(f"    Endpoint: {endpoint}")
                    print(f"    Payload: {attack_data['payload'][:50]}...")
                    print(f"    Isolation Forest: {iso_result.get('message', 'N/A')}")
                    print(f"    Random Forest: {rf_result.get('prediction', 'N/A')}")
                    print("-" * 50)
            
            return True
            
        except Exception as e:
            print(f"Ошибка отправки в ML: {e}")
            return False
    
    def run_monitoring(self):
        """Запуск мониторинга"""
        print("Запуск мониторинга Juice Shop...")
        print(f"Juice Shop: {self.juice_shop_url}")
        print("Нажмите Ctrl+C для остановки\n")
        
        request_count = 0
        attack_count = 0
        
        while self.running:
            try:
                request_count += 1
                
                # Генерируем симулированный трафик
                endpoint, attack_data = self.generate_simulated_traffic()
                
                # Отправляем в ML
                if attack_data["type"] != "normal":
                    attack_count += 1
                
                self.send_to_ml(endpoint, attack_data)
                
                # Статистика каждые 10 запросов
                if request_count % 10 == 0:
                    print(f"\n[Статистика] Запросов: {request_count}, Атак: {attack_count}")
                
                time.sleep(random.uniform(0.5, 2.0))
                
            except KeyboardInterrupt:
                print("\nОстановка мониторинга...")
                self.running = False
                break
            except Exception as e:
                print(f"Ошибка в мониторе: {e}")
                time.sleep(1)
        
        print(f"\nФинальная статистика: {request_count} запросов, {attack_count} атак")

def main():
    monitor = JuiceShopMonitor()
    monitor.run_monitoring()

if __name__ == "__main__":
    main()
