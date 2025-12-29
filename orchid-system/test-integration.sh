#!/bin/bash

# Test Orchid system integration

echo "Testing Orchid System Integration..."

# Test 1: Check if services are running
echo "1. Checking services..."
services=("rabbitmq" "postgres" "redis" "orchid-core")
for service in "${services[@]}"; do
    if docker ps | grep -q $service; then
        echo "   ✓ $service is running"
    else
        echo "   ✗ $service is NOT running"
    fi
done

# Test 2: Test API endpoints
echo "2. Testing API endpoints..."
if curl -s http://localhost:8080/health | grep -q "healthy"; then
    echo "   ✓ Core API is healthy"
else
    echo "   ✗ Core API is not responding"
fi

# Test 3: Test ML services
echo "3. Testing ML services..."
if curl -s http://localhost:8001/health | grep -q "healthy"; then
    echo "   ✓ Isolation Forest service is healthy"
else
    echo "   ✗ Isolation Forest service is not responding"
fi

# Test 4: Send test request
echo "4. Sending test request..."
TEST_REQUEST='{
    "features": {
        "request_length": 450,
        "param_count": 5,
        "special_char_ratio": 0.15,
        "url_depth": 3,
        "user_agent_length": 120,
        "content_length": 2048,
        "request_time_seconds": 0.5,
        "status_code": 200
    },
    "metadata": {
        "source": "test"
    }
}'

response=$(curl -s -X POST http://localhost:8001/predict \
    -H "Content-Type: application/json" \
    -d "$TEST_REQUEST")

if echo $response | grep -q "anomaly_score"; then
    echo "   ✓ ML prediction successful"
    echo "   Response: $response"
else
    echo "   ✗ ML prediction failed"
fi

echo ""
echo "Integration test completed!"
