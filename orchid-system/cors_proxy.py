#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from urllib.parse import urlparse
import json

class CORSProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Проксируем запросы к ML сервисам
        if self.path.startswith('/proxy/'):
            try:
                # Извлекаем порт из URL
                port = self.path.split('/')[2]
                target_url = f'http://localhost:{port}/health'
                
                response = requests.get(target_url, timeout=2)
                
                self.send_response(response.status_code)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                
                self.wfile.write(response.content)
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'CORS Proxy Running')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), CORSProxyHandler)
    print('CORS Proxy running on port 8080...')
    server.serve_forever()
