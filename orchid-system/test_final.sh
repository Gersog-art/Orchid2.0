#!/bin/bash

echo "=== FINAL ORCHID SYSTEM TEST ==="
echo ""

# Проверяем порты
echo "1. Проверка открытых портов:"
ports=(8001 8002 3000 3001 8080)
for port in "${ports[@]}"; do
    if nc -z localhost $port 2>/dev/null; then
        echo "  ✓ Порт $port открыт"
    else
        echo "  ✗ Порт $port закрыт"
    fi
done

echo ""
echo "2. Проверка HTTP сервисов:"
services=(
    "http://localhost:8001/health:Isolation Forest"
    "http://localhost:8002/health:Random Forest"
    "http://localhost:3000:Admin Panel"
    "http://localhost:3001:Juice Shop"
    "http://localhost:8080:Proxy Server"
)

for service in "${services[@]}"; do
    url=$(echo $service | cut -d: -f1-2)
    name=$(echo $service | cut -d: -f3)
    
    if curl -s --head $url > /dev/null 2>&1; then
        echo "  ✓ $name доступен"
    else
        echo "  ✗ $name не доступен"
    fi
done

echo ""
echo "3. Проверка CORS заголовков:"
echo "   Isolation Forest CORS:"
curl -s -I http://localhost:8001/health | grep -i "access-control" || echo "   Нет CORS заголовков"

echo ""
echo "4. Тест обнаружения атаки:"
echo '{"test": "attack"}' | curl -s -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d @- | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('   Результат:', data.get('message', 'No message'))
    print('   Anomaly:', data.get('is_anomaly', 'Unknown'))
except:
    print('   ❌ Ошибка запроса')
"

echo ""
echo "=== ИТОГИ ==="
echo "Если все порты открыты и сервисы доступны:"
echo "1. Откройте http://localhost:3000"
echo "2. Нажмите 'Force Check'"
echo "3. Должны появиться зеленые статусы ML сервисов"
echo "4. Нажмите 'Test ML Services' для проверки обнаружения"
echo ""
echo "Если ML сервисы красные, но порты открыты - это CORS проблема в браузере."
echo "В этом случае используйте кнопку 'Test ML Services' - она должна работать."
