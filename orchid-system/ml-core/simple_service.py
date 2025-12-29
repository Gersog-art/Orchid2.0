#!/usr/bin/env python3
"""
Упрощенный ML сервис для тестирования
Работает на порту 8000, поддерживает CORS
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time

class SimpleMLHandler(BaseHTTPRequestHandler):
    """Обработчик для ML сервиса"""
    
    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, HEAD')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()
    
    def do_HEAD(self):
        """Обработка HEAD запросов"""
        if self.path == '/health':
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
        else:
            self.send_response(200)
            self._send_cors_headers()
            self.end_headers()
    
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            response = {
                "status": "healthy",
                "service": self.server.service_name,
                "timestamp": time.time(),
                "endpoints": ["/health", "/predict"],
                "version": "1.0.0"
            }
            self.wfile.write(json.dumps(response).encode())
        
        elif self.path == '/':
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"{self.server.service_name} ML Service".encode())
        
        else:
            self.send_response(404)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        if self.path == '/predict':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length:
                post_data = self.rfile.read(content_length)
            else:
                post_data = b'{}'
            
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # Простая логика определения атаки
            try:
                data = json.loads(post_data.decode())
                is_attack = False
                attack_type = "normal"
                
                if data:
                    data_str = str(data).lower()
                    if "'" in data_str or "union" in data_str:
                        is_attack = True
                        attack_type = "sqli"
                    elif "<script>" in data_str:
                        is_attack = True
                        attack_type = "xss"
                
                response = {
                    "is_anomaly": is_attack,
                    "anomaly_score": -0.9 if is_attack else 0.1,
                    "prediction": attack_type,
                    "confidence": 0.95 if is_attack else 0.05,
                    "service": self.server.service_name,
                    "timestamp": time.time()
                }
            except:
                response = {"error": "Invalid JSON", "service": self.server.service_name}
            
            self.wfile.write(json.dumps(response).encode())
        
        else:
            self.send_response(404)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

class MLServer(HTTPServer):
    """Кастомный сервер с именем сервиса"""
    def __init__(self, *args, service_name="ML Service", **kwargs):
        self.service_name = service_name
        super().__init__(*args, **kwargs)

def run_service(port=8000, service_name="ML Service"):
    """Запуск сервиса"""
    server = MLServer(('0.0.0.0', port), SimpleMLHandler, service_name=service_name)
    print(f"{service_name} запущен на порту {port}")
    print(f"Доступен по http://localhost:{port}/health")
    server.serve_forever()

if __name__ == '__main__':
    import sys
    port = 8000
    service_name = "Generic ML"
    
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except:
            pass
    
    if len(sys.argv) > 2:
        service_name = sys.argv[2]
    
    run_service(port, service_name)
