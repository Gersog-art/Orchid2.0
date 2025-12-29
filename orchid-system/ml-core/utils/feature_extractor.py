"""
Feature extraction utilities
"""
import json
import numpy as np

def extract_http_features(request_data: dict) -> np.ndarray:
    """
    Extract features from HTTP request data
    """
    features = []
    
    # 1. Request length
    request_str = json.dumps(request_data.get('request', {}))
    features.append(len(request_str))
    
    # 2. Parameter count
    params = request_data.get('request', {}).get('params', {})
    features.append(len(params))
    
    # 3. Special character ratio in body
    body = request_data.get('request', {}).get('body', '')
    if body and isinstance(body, str):
        special_chars = sum(1 for c in body if not c.isalnum() and not c.isspace())
        features.append(special_chars / max(len(body), 1))
    else:
        features.append(0.0)
    
    # 4. URL depth
    url = request_data.get('request', {}).get('url', '')
    features.append(url.count('/'))
    
    # 5. User agent length
    ua = request_data.get('request', {}).get('headers', {}).get('user-agent', '')
    features.append(len(ua))
    
    # 6. Content length
    features.append(int(request_data.get('request', {}).get('headers', {}).get('content-length', 0)))
    
    # 7. Request time
    features.append(request_data.get('metadata', {}).get('request_time', 0))
    
    # 8. Error status code
    status = request_data.get('metadata', {}).get('status_code', 200)
    features.append(1.0 if 400 <= status < 600 else 0.0)
    
    return np.array(features)
