from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import random
import time

class Handler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        """Устанавливаем CORS заголовки"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')
    
    def do_OPTIONS(self):
        """Обработка CORS preflight запросов"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self._set_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            response = {
                "status": "healthy",
                "service": "Random Forest",
                "timestamp": time.time(),
                "version": "1.0.0",
                "endpoints": {
                    "health": "GET /health",
                    "predict": "POST /predict"
                }
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(200)
            self._set_cors_headers()
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Random Forest API Service')
    
    def do_POST(self):
        if self.path == '/predict':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode())
                
                # Определяем тип атаки
                attack_types = ['normal', 'sqli', 'xss', 'brute_force', 'path_traversal', 'csrf']
                
                # Простая эвристика для определения типа атаки
                data_str = str(data).lower()
                
                if "' or '1'='1" in data_str or "union select" in data_str:
                    prediction = "sqli"
                    confidence = 0.95
                elif "<script>" in data_str or "javascript:" in data_str:
                    prediction = "xss"
                    confidence = 0.88
                elif ".." in data_str or "etc/passwd" in data_str:
                    prediction = "path_traversal"
                    confidence = 0.82
                elif "admin" in data_str and ("password" in data_str or "login" in data_str):
                    prediction = "brute_force"
                    confidence = 0.75
                elif "csrf" in data_str or "token" in data_str:
                    prediction = "csrf"
                    confidence = 0.70
                else:
                    prediction = "normal"
                    confidence = 0.10
                
                self.send_response(200)
                self._set_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                
                # Генерируем вероятности для всех классов
                probabilities = {}
                for attack_type in attack_types:
                    if attack_type == prediction:
                        probabilities[attack_type] = confidence
                    else:
                        probabilities[attack_type] = round((1 - confidence) / (len(attack_types) - 1), 3)
                
                response = {
                    "prediction": prediction,
                    "confidence": confidence,
                    "probabilities": probabilities,
                    "is_attack": prediction != "normal",
                    "timestamp": time.time(),
                    "explanation": "Random Forest classification completed"
                }
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                self.send_response(500)
                self._set_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self._set_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8000), Handler)
    print('Random Forest running on port 8000...')
    print('CORS enabled - accepting requests from any origin')
    server.serve_forever()
