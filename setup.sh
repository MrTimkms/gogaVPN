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

# Функция для генерации SECRET_KEY
generate_secret_key() {
    if command -v openssl &> /dev/null; then
        openssl rand -hex 32
    else
        # Fallback если openssl не установлен
        python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "change-me-in-production-$(date +%s)"
    fi
}

# Создание или обновление .env файла
if [ ! -f .env ]; then
    echo "📝 Настройка конфигурации..."
    echo ""
    
    # Запрос BOT_TOKEN
    echo "🤖 Telegram Bot Token"
    echo "   Получите у @BotFather в Telegram: https://t.me/BotFather"
    echo "   Команда: /newbot"
    echo ""
    read -p "Введите BOT_TOKEN: " BOT_TOKEN
    while [ -z "$BOT_TOKEN" ]; do
        echo "❌ BOT_TOKEN не может быть пустым!"
        read -p "Введите BOT_TOKEN: " BOT_TOKEN
    done
    
    # Запрос ADMIN_TELEGRAM_IDS
    echo ""
    echo "👤 Telegram ID администратора"
    echo "   Получите у @userinfobot в Telegram: https://t.me/userinfobot"
    echo "   Команда: /start"
    echo ""
    read -p "Введите ADMIN_TELEGRAM_IDS: " ADMIN_TELEGRAM_IDS
    while [ -z "$ADMIN_TELEGRAM_IDS" ]; do
        echo "❌ ADMIN_TELEGRAM_IDS не может быть пустым!"
        read -p "Введите ADMIN_TELEGRAM_IDS: " ADMIN_TELEGRAM_IDS
    done
    
    # Запрос TELEGRAM_BOT_NAME
    echo ""
    echo "📝 Имя бота (без символа @)"
    echo "   Например: my_vpn_bot"
    echo ""
    read -p "Введите TELEGRAM_BOT_NAME (или нажмите Enter для автоматического определения): " TELEGRAM_BOT_NAME
    
    # Генерация SECRET_KEY
    SECRET_KEY=$(generate_secret_key)
    
    # Создание .env файла
    cat > .env << EOF
# Database (для Docker используется PostgreSQL из docker-compose)
DATABASE_URL=postgresql://vpn_user:vpn_password@db:5432/vpn_billing

# Telegram Bot
BOT_TOKEN=${BOT_TOKEN}
ADMIN_TELEGRAM_IDS=${ADMIN_TELEGRAM_IDS}

# Telegram Login Widget
TELEGRAM_BOT_NAME=${TELEGRAM_BOT_NAME:-your_bot_username}

# Server
SECRET_KEY=${SECRET_KEY}
DEBUG=True

# Billing
DEFAULT_SUBSCRIPTION_PRICE=100
EOF
    
    echo ""
    echo "✅ Файл .env создан и настроен!"
    echo ""
else
    echo "✅ Файл .env уже существует"
    echo ""
    read -p "Хотите обновить настройки? (y/n): " UPDATE_ENV
    if [[ "$UPDATE_ENV" =~ ^[Yy]$ ]]; then
        # Запрос BOT_TOKEN
        echo ""
        read -p "Введите новый BOT_TOKEN (или Enter чтобы оставить текущий): " BOT_TOKEN
        if [ ! -z "$BOT_TOKEN" ]; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s|^BOT_TOKEN=.*|BOT_TOKEN=${BOT_TOKEN}|" .env
            else
                # Linux
                sed -i "s|^BOT_TOKEN=.*|BOT_TOKEN=${BOT_TOKEN}|" .env
            fi
        fi
        
        # Запрос ADMIN_TELEGRAM_IDS
        read -p "Введите новый ADMIN_TELEGRAM_IDS (или Enter чтобы оставить текущий): " ADMIN_TELEGRAM_IDS
        if [ ! -z "$ADMIN_TELEGRAM_IDS" ]; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s|^ADMIN_TELEGRAM_IDS=.*|ADMIN_TELEGRAM_IDS=${ADMIN_TELEGRAM_IDS}|" .env
            else
                sed -i "s|^ADMIN_TELEGRAM_IDS=.*|ADMIN_TELEGRAM_IDS=${ADMIN_TELEGRAM_IDS}|" .env
            fi
        fi
        
        # Запрос TELEGRAM_BOT_NAME
        read -p "Введите новый TELEGRAM_BOT_NAME (или Enter чтобы оставить текущий): " TELEGRAM_BOT_NAME
        if [ ! -z "$TELEGRAM_BOT_NAME" ]; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s|^TELEGRAM_BOT_NAME=.*|TELEGRAM_BOT_NAME=${TELEGRAM_BOT_NAME}|" .env
            else
                sed -i "s|^TELEGRAM_BOT_NAME=.*|TELEGRAM_BOT_NAME=${TELEGRAM_BOT_NAME}|" .env
            fi
        fi
        
        echo "✅ Настройки обновлены!"
    fi
    echo ""
fi

echo "🐳 Запуск Docker контейнеров..."
echo ""

# Запуск через docker-compose или docker compose
if docker compose version &> /dev/null; then
    docker compose up -d --build
else
    docker-compose up -d --build
fi

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Ошибка запуска Docker!"
    exit 1
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
