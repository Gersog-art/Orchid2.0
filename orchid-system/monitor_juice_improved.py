#!/usr/bin/env python3
import requests
import json
import time
import random
from datetime import datetime
import sqlite3
import threading

class JuiceShopMonitor:
    def __init__(self):
        self.juice_shop_url = "http://localhost:3001"
        self.ml_isolation_url = "http://localhost:8001/predict"
        self.ml_random_url = "http://localhost:8002/predict"
        self.admin_url = "http://localhost:3000"
        self.running = True
        self.attack_log = []
        self.db_file = "attacks.db"
        
        # Инициализируем БД
        self.init_db()
        
    def init_db(self):
        """Инициализация SQLite базы данных для логов"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                attack_type TEXT NOT NULL,
                source_ip TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                payload TEXT,
                isolation_result TEXT,
                random_result TEXT,
                detected BOOLEAN DEFAULT 1
            )
        ''')
        conn.commit()
        conn.close()
        print(f"База данных инициализирована: {self.db_file}")
    
    def log_attack(self, attack_data, endpoint, iso_result, rf_result):
        """Записываем атаку в БД и в память"""
        attack_log_entry = {
            'timestamp': datetime.now().isoformat(),
            'attack_type': attack_data['type'],
            'source_ip': f"192.168.1.{random.randint(1, 255)}",
            'endpoint': endpoint,
            'payload': attack_data['payload'][:100],
            'iso_result': str(iso_result.get('message', 'N/A')),
            'rf_result': str(rf_result.get('prediction', 'N/A')),
            'detected': iso_result.get('is_anomaly', False) or rf_result.get('is_attack', False)
        }
        
        self.attack_log.append(attack_log_entry)
        
        # Сохраняем в БД
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO attacks (timestamp, attack_type, source_ip, endpoint, payload, isolation_result, random_result, detected)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            attack_log_entry['timestamp'],
            attack_log_entry['attack_type'],
            attack_log_entry['source_ip'],
            attack_log_entry['endpoint'],
            attack_log_entry['payload'],
            attack_log_entry['iso_result'],
            attack_log_entry['rf_result'],
            attack_log_entry['detected']
        ))
        conn.commit()
        conn.close()
        
        # Выводим в консоль цветной лог
        if attack_log_entry['detected']:
            print(f"\033[91m[!] Атака обнаружена: {attack_data['type']}\033[0m")
        else:
            print(f"\033[93m[~] Атака не обнаружена: {attack_data['type']}\033[0m")
        
        print(f"    Endpoint: {endpoint}")
        print(f"    Payload: {attack_data['payload'][:50]}...")
        print(f"    Isolation Forest: {iso_result.get('message', 'N/A')}")
        print(f"    Random Forest: {rf_result.get('prediction', 'N/A')}")
        print(f"    Source IP: {attack_log_entry['source_ip']}")
        print("-" * 50)
    
    def generate_simulated_traffic(self):
        """Генерируем симулированный трафик атак"""
        endpoints = [
            "/rest/user/login",
            "/api/Products",
            "/profile",
            "/#/search",
            "/rest/basket",
            "/rest/admin/application-configuration",
            "/ftp",
            "/redirect"
        ]
        
        attacks = [
            {"type": "sqli", "payload": "' UNION SELECT username, password FROM Users--"},
            {"type": "sqli", "payload": "' OR '1'='1' --"},
            {"type": "xss", "payload": "<img src=x onerror=alert(1)>"},
            {"type": "xss", "payload": "<script>document.location='http://evil.com'</script>"},
            {"type": "lfi", "payload": "../../../../etc/passwd"},
            {"type": "rce", "payload": "; cat /etc/shadow"},
            {"type": "rce", "payload": "| ls -la /"},
            {"type": "xxe", "payload": "<!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>"},
            {"type": "idor", "payload": "/rest/user/1"},
            {"type": "idor", "payload": "/api/Baskets/1"},
            {"type": "ssrf", "payload": "http://169.254.169.254/latest/meta-data/"},
            {"type": "ssrf", "payload": "http://internal.admin.local"},
        ]
        
        normal_requests = [
            {"type": "normal", "payload": "product=1"},
            {"type": "normal", "payload": "search=apple"},
            {"type": "normal", "payload": "email=user@test.com"},
            {"type": "normal", "payload": "page=1"},
            {"type": "normal", "payload": "category=juice"},
            {"type": "normal", "payload": "sort=price"},
        ]
        
        # 40% chance of attack
        if random.random() < 0.4:
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
                timeout=2
            )
            
            # Отправляем в Random Forest
            rf_response = requests.post(
                self.ml_random_url,
                json=ml_data,
                timeout=2
            )
            
            iso_result = iso_response.json() if iso_response.status_code == 200 else {"error": iso_response.status_code}
            rf_result = rf_response.json() if rf_response.status_code == 200 else {"error": rf_response.status_code}
            
            # Логируем атаку
            self.log_attack(attack_data, endpoint, iso_result, rf_result)
            
            return True
            
        except Exception as e:
            print(f"\033[90m[DEBUG] Ошибка отправки в ML: {e}\033[0m")
            return False
    
    def show_statistics(self, request_count, attack_count):
        """Показываем статистику в красивом формате"""
        print("\n" + "=" * 60)
        print("\033[94m" + " "*20 + "ORCHID SECURITY MONITOR" + " "*20 + "\033[0m")
        print("=" * 60)
        print(f"📊 Статистика:")
        print(f"   Всего запросов:    \033[96m{request_count}\033[0m")
        print(f"   Обнаружено атак:   \033[91m{attack_count}\033[0m")
        print(f"   Juice Shop:        \033[92mhttp://localhost:3001\033[0m")
        print(f"   Админ панель:      \033[92mhttp://localhost:3000\033[0m")
        print("=" * 60)
    
    def run_monitoring(self):
        """Запуск мониторинга"""
        print("\033[94m" + "="*60 + "\033[0m")
        print("\033[94m" + " "*15 + "ORCHID SECURITY SYSTEM MONITOR" + " "*15 + "\033[0m")
        print("\033[94m" + "="*60 + "\033[0m")
        print("\033[93mЗапуск мониторинга Juice Shop...\033[0m")
        print(f"\033[93mJuice Shop URL: {self.juice_shop_url}\033[0m")
        print("\033[93mНажмите Ctrl+C для остановки\033[0m\n")
        
        request_count = 0
        attack_count = 0
        
        # Стартовый тест ML сервисов
        print("\033[95mТестируем ML сервисы...\033[0m")
        try:
            iso_health = requests.get("http://localhost:8001/health", timeout=2)
            rf_health = requests.get("http://localhost:8002/health", timeout=2)
            print(f"Isolation Forest: {'✓' if iso_health.status_code == 200 else '✗'}")
            print(f"Random Forest:    {'✓' if rf_health.status_code == 200 else '✗'}")
        except:
            print("ML сервисы недоступны!")
        
        print("\n" + "="*60 + "\n")
        
        while self.running:
            try:
                request_count += 1
                
                # Генерируем симулированный трафик
                endpoint, attack_data = self.generate_simulated_traffic()
                
                # Отправляем в ML
                if attack_data["type"] != "normal":
                    attack_count += 1
                
                self.send_to_ml(endpoint, attack_data)
                
                # Показываем статистику каждые 5 запросов
                if request_count % 5 == 0:
                    self.show_statistics(request_count, attack_count)
                
                # Случайная задержка между запросами
                time.sleep(random.uniform(0.3, 1.5))
                
            except KeyboardInterrupt:
                print("\n\033[93mОстановка мониторинга...\033[0m")
                self.running = False
                break
            except Exception as e:
                print(f"\033[90m[DEBUG] Ошибка: {e}\033[0m")
                time.sleep(1)
        
        # Финальная статистика
        print("\n" + "="*60)
        print("\033[92m" + " "*20 + "МОНИТОРИНГ ЗАВЕРШЕН" + " "*20 + "\033[0m")
        print("="*60)
        print(f"\033[96mФинальная статистика:\033[0m")
        print(f"   Всего запросов:    {request_count}")
        print(f"   Обнаружено атак:   {attack_count}")
        print(f"   Логов в БД:        {len(self.attack_log)}")
        print("="*60)
        print(f"\033[92mБаза данных атак: {self.db_file}\033[0m")
        print(f"\033[92mДля просмотра: sqlite3 {self.db_file} 'SELECT * FROM attacks LIMIT 10;'\033[0m")

def main():
    monitor = JuiceShopMonitor()
    monitor.run_monitoring()

if __name__ == "__main__":
    main()
