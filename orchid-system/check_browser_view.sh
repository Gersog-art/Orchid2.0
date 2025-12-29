#!/bin/bash

echo "=== ПРОВЕРКА ДАННЫХ, КОТОРЫЕ ПОЛУЧАЕТ БРАУЗЕР ==="

echo -e "\n1. Прямой запрос к ML сервисам (как браузер):"
echo "Isolation Forest:"
curl -s "http://localhost:8001/health" \
  -H "Origin: http://localhost:3000" \
  -H "User-Agent: Mozilla/5.0 (Test)" | python3 -m json.tool 2>/dev/null || echo "   Не JSON ответ"

echo -e "\nRandom Forest:"
curl -s "http://localhost:8002/health" \
  -H "Origin: http://localhost:3000" \
  -H "User-Agent: Mozilla/5.0 (Test)" | python3 -m json.tool 2>/dev/null || echo "   Не JSON ответ"

echo -e "\n2. Проверка OPTIONS запроса (CORS preflight):"
echo "OPTIONS к Isolation Forest:"
curl -s -X OPTIONS "http://localhost:8001/health" \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" -I 2>&1 | grep -i "access-control" || echo "   Нет CORS заголовков"

echo -e "\n3. Проверка через прокси (если используется):"
curl -s "http://localhost:8080/api/proxy/8001/health" 2>/dev/null && echo "✓ Прокси работает" || echo "✗ Прокси не отвечает"

echo -e "\n4. Проверка заголовков ответов:"
echo "Isolation Forest headers:"
curl -s -I "http://localhost:8001/health" | grep -E "(HTTP|Access-Control|Content-Type)" | head -10

echo -e "\n5. Проверка, что сервисы действительно слушают порты:"
echo "Сетевые соединения:"
docker-compose exec ml-isolation netstat -tlnp 2>/dev/null | grep :8000 || echo "   Не слушает порт 8000 в контейнере"
docker-compose exec ml-random netstat -tlnp 2>/dev/null | grep :8000 || echo "   Не слушает порт 8000 в контейнере"

echo -e "\n6. Логи контейнеров (последние 5 строк):"
echo "Isolation Forest logs:"
docker-compose logs --tail=5 ml-isolation 2>/dev/null | grep -v "^\s*$" || echo "   Нет логов"
echo -e "\nRandom Forest logs:"
docker-compose logs --tail=5 ml-random 2>/dev/null | grep -v "^\s*$" || echo "   Нет логов"
