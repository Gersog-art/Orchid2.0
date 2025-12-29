#!/bin/bash
echo "=== Быстрая проверка Orchid ==="
echo ""
echo "1. Контейнеры:"
docker-compose ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "2. ML сервисы:"
curl -s http://localhost:8001/health | grep -o '"status":"[^"]*"' || echo "✗ Isolation Forest"
curl -s http://localhost:8002/health | grep -o '"status":"[^"]*"' || echo "✗ Random Forest"

echo ""
echo "3. Веб-интерфейсы:"
echo "   Админка:    http://localhost:3000"
echo "   Juice Shop: http://localhost:3001"

echo ""
echo "4. Тест обнаружения:"
echo '{"test":"attack"}' | curl -s -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" -d @- | grep -o '"is_anomaly":[^,]*' || echo "✗ Predict failed"

echo ""
echo "=== Если выше все зелёное - система работает! ==="
