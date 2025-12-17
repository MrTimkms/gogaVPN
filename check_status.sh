#!/bin/bash

echo "🔍 Проверка статуса VPN Billing System"
echo "========================================"
echo ""

# Проверка Docker
echo "1️⃣ Проверка Docker..."
if command -v docker &> /dev/null; then
    echo "   ✅ Docker установлен: $(docker --version)"
else
    echo "   ❌ Docker не установлен"
    exit 1
fi

if docker compose version &> /dev/null || docker-compose version &> /dev/null; then
    echo "   ✅ Docker Compose установлен"
else
    echo "   ❌ Docker Compose не установлен"
    exit 1
fi
echo ""

# Проверка контейнеров
echo "2️⃣ Проверка контейнеров..."
cd ~/gogaVPN 2>/dev/null || cd gogaVPN 2>/dev/null || { echo "   ⚠️ Не найден каталог проекта"; exit 1; }

if docker compose ps &> /dev/null; then
    docker compose ps
else
    docker-compose ps
fi
echo ""

# Проверка статуса сервисов
echo "3️⃣ Статус сервисов..."
CONTAINERS=$(docker compose ps --format json 2>/dev/null || docker-compose ps --format json 2>/dev/null)

if echo "$CONTAINERS" | grep -q "running"; then
    echo "   ✅ Контейнеры запущены"
else
    echo "   ⚠️ Некоторые контейнеры не запущены"
fi
echo ""

# Проверка портов
echo "4️⃣ Проверка портов..."
if command -v netstat &> /dev/null; then
    if netstat -tuln 2>/dev/null | grep -q ":8000\|:8001"; then
        echo "   ✅ Порт 8000 или 8001 открыт"
        netstat -tuln 2>/dev/null | grep ":8000\|:8001"
    else
        echo "   ⚠️ Порт не найден"
    fi
elif command -v ss &> /dev/null; then
    if ss -tuln 2>/dev/null | grep -q ":8000\|:8001"; then
        echo "   ✅ Порт 8000 или 8001 открыт"
        ss -tuln 2>/dev/null | grep ":8000\|:8001"
    else
        echo "   ⚠️ Порт не найден"
    fi
fi
echo ""

# Проверка доступности веб-интерфейса
echo "5️⃣ Проверка веб-интерфейса..."
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 2>/dev/null || curl -s -o /dev/null -w "%{http_code}" http://localhost:8001 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        echo "   ✅ Веб-интерфейс доступен (HTTP $HTTP_CODE)"
    else
        echo "   ⚠️ Веб-интерфейс недоступен (HTTP $HTTP_CODE)"
    fi
else
    echo "   ⚠️ curl не установлен, проверка пропущена"
fi
echo ""

# Проверка логов на ошибки
echo "6️⃣ Проверка логов (последние 20 строк)..."
echo "   Backend:"
docker compose logs --tail=5 backend 2>/dev/null | tail -3 || docker-compose logs --tail=5 backend 2>/dev/null | tail -3
echo ""
echo "   Bot:"
docker compose logs --tail=5 bot 2>/dev/null | tail -3 || docker-compose logs --tail=5 bot 2>/dev/null | tail -3
echo ""

# Проверка .env файла
echo "7️⃣ Проверка конфигурации..."
if [ -f .env ]; then
    echo "   ✅ Файл .env существует"
    if grep -q "BOT_TOKEN=" .env && ! grep -q "BOT_TOKEN=your_telegram_bot_token_here" .env; then
        echo "   ✅ BOT_TOKEN настроен"
    else
        echo "   ⚠️ BOT_TOKEN не настроен"
    fi
    if grep -q "ADMIN_TELEGRAM_IDS=" .env && ! grep -q "ADMIN_TELEGRAM_IDS=123456789" .env; then
        echo "   ✅ ADMIN_TELEGRAM_IDS настроен"
    else
        echo "   ⚠️ ADMIN_TELEGRAM_IDS не настроен"
    fi
else
    echo "   ❌ Файл .env не найден"
fi
echo ""

# Итоговая информация
echo "📋 Итоговая информация:"
echo "=========================="
echo ""
echo "🌐 Веб-интерфейс:"
if netstat -tuln 2>/dev/null | grep -q ":8001"; then
    echo "   http://$(hostname -I | awk '{print $1}'):8001"
elif netstat -tuln 2>/dev/null | grep -q ":8000"; then
    echo "   http://$(hostname -I | awk '{print $1}'):8000"
else
    echo "   http://ваш_сервер_ip:8000 (или 8001)"
fi
echo ""
echo "📚 API документация:"
if netstat -tuln 2>/dev/null | grep -q ":8001"; then
    echo "   http://$(hostname -I | awk '{print $1}'):8001/docs"
elif netstat -tuln 2>/dev/null | grep -q ":8000"; then
    echo "   http://$(hostname -I | awk '{print $1}'):8000/docs"
else
    echo "   http://ваш_сервер_ip:8000/docs (или 8001)"
fi
echo ""
echo "⚙️ Админ-панель:"
if netstat -tuln 2>/dev/null | grep -q ":8001"; then
    echo "   http://$(hostname -I | awk '{print $1}'):8001/admin"
elif netstat -tuln 2>/dev/null | grep -q ":8000"; then
    echo "   http://$(hostname -I | awk '{print $1}'):8000/admin"
else
    echo "   http://ваш_сервер_ip:8000/admin (или 8001)"
fi
echo ""
echo "📊 Полезные команды:"
echo "   docker compose logs -f          # Просмотр всех логов"
echo "   docker compose logs -f bot     # Логи бота"
echo "   docker compose logs -f backend # Логи API"
echo "   docker compose ps              # Статус контейнеров"
echo "   docker compose restart         # Перезапуск"
echo ""

