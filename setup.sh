#!/bin/bash

echo "🔧 Настройка проекта VPN Billing System"
echo "========================================"
echo ""

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен!"
    echo "Установите Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose не установлен!"
    echo "Установите Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker найден"
echo ""

# Создание .env файла если его нет
if [ ! -f .env ]; then
    echo "📝 Создание файла .env..."
    
    if [ -f env.example.txt ]; then
        cp env.example.txt .env
    else
        cat > .env << EOF
# Database (для Docker используется PostgreSQL из docker-compose)
DATABASE_URL=postgresql://vpn_user:vpn_password@db:5432/vpn_billing

# Telegram Bot
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_TELEGRAM_IDS=123456789

# Telegram Login Widget
TELEGRAM_BOT_NAME=your_bot_username

# Server
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=True

# Billing
DEFAULT_SUBSCRIPTION_PRICE=100
EOF
    fi
    
    echo "✅ Файл .env создан"
    echo ""
    echo "⚠️  ВАЖНО: Отредактируйте файл .env и укажите:"
    echo "   - BOT_TOKEN (получите у @BotFather в Telegram)"
    echo "   - ADMIN_TELEGRAM_IDS (ваш Telegram ID)"
    echo "   - TELEGRAM_BOT_NAME (имя вашего бота без @)"
    echo ""
    read -p "Нажмите Enter после редактирования .env файла..."
else
    echo "✅ Файл .env уже существует"
fi

echo ""
echo "🐳 Запуск Docker контейнеров..."
echo ""

# Запуск через docker-compose или docker compose
if docker compose version &> /dev/null; then
    docker compose up -d --build
else
    docker-compose up -d --build
fi

echo ""
echo "⏳ Ожидание запуска сервисов..."
sleep 5

echo ""
echo "✅ Проект запущен!"
echo ""
echo "📋 Доступные сервисы:"
echo "   - Веб-интерфейс: http://localhost:8000"
echo "   - API документация: http://localhost:8000/docs"
echo "   - Админ-панель: http://localhost:8000/admin"
echo ""
echo "📊 Просмотр логов:"
echo "   docker compose logs -f"
echo ""
echo "🛑 Остановка:"
echo "   docker compose down"
echo ""

