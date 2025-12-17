#!/bin/bash

echo "🆕 Полная установка с нуля"
echo "=========================="
echo ""

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен!"
    echo "Установите Docker: curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh"
    exit 1
fi

echo "✅ Docker найден"
echo ""

# Удаление старой версии если есть
if [ -d ~/gogaVPN ]; then
    read -p "⚠️  Найдена старая версия. Удалить? (y/n): " REMOVE_OLD
    if [[ "$REMOVE_OLD" =~ ^[Yy]$ ]]; then
        echo "Удаление старой версии..."
        cd ~/gogaVPN
        docker compose down -v 2>/dev/null
        cd ~
        rm -rf ~/gogaVPN
        echo "✅ Старая версия удалена"
    fi
fi

echo ""
echo "1️⃣ Клонирование проекта..."
cd ~
git clone https://github.com/MrTimkms/gogaVPN.git
cd gogaVPN
echo "✅ Проект клонирован"
echo ""

echo "2️⃣ Настройка конфигурации..."
chmod +x setup.sh
./setup.sh

echo ""
echo "3️⃣ Запуск..."
docker compose up -d --build

echo ""
echo "⏳ Ожидание запуска (30 секунд)..."
sleep 30

echo ""
echo "4️⃣ Проверка статуса..."
docker compose ps

echo ""
echo "✅ Установка завершена!"
echo ""
echo "📋 Полезные команды:"
echo "   docker compose logs -f          # Логи"
echo "   docker compose ps               # Статус"
echo "   docker compose restart          # Перезапуск"
echo ""
echo "🌐 Веб-интерфейс:"
echo "   http://$(hostname -I | awk '{print $1}'):8085"
echo ""

