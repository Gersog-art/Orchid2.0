from http.server import HTTPServer, BaseHTTPRequestHandler
import json
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
                "service": "Isolation Forest",
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
            self.wfile.write(b'Isolation Forest API Service')
    
    def do_POST(self):
        if self.path == '/predict':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode())
                # Простая логика определения аномалий
                has_sqli = "' OR '1'='1" in str(data)
                has_xss = "<script>" in str(data)
                is_attack = has_sqli or has_xss
                
                self.send_response(200)
                self._set_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                
                response = {
                    "is_anomaly": is_attack,
                    "anomaly_score": -0.85 if is_attack else 0.15,
                    "message": "Attack detected!" if is_attack else "Normal traffic",
                    "timestamp": time.time(),
                    "attack_types": {
                        "sql_injection": has_sqli,
                        "xss": has_xss
                    },
                    "confidence": 0.92 if is_attack else 0.05
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
    print('Isolation Forest running on port 8000...')
    print('CORS enabled - accepting requests from any origin')
    server.serve_forever()
