#!/bin/bash

echo "🆕 Полная установка VPN Billing System с нуля"
echo "=============================================="
echo ""

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "📦 Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo apt install docker-compose-plugin -y
    sudo usermod -aG docker $USER
    echo "✅ Docker установлен"
    echo ""
else
    echo "✅ Docker уже установлен"
    echo ""
fi

# Удаление старой версии если есть
if [ -d ~/gogaVPN ]; then
    echo "🗑️  Удаление старой версии..."
    cd ~/gogaVPN
    docker compose down -v 2>/dev/null
    cd ~
    rm -rf ~/gogaVPN
    echo "✅ Старая версия удалена"
    echo ""
fi

# Клонирование проекта
echo "📥 Клонирование проекта..."
cd ~
git clone https://github.com/MrTimkms/gogaVPN.git
cd gogaVPN
echo "✅ Проект клонирован"
echo ""

# Настройка
echo "⚙️  Настройка конфигурации..."
chmod +x setup.sh
./setup.sh

echo ""
echo "✅ Установка завершена!"
echo ""
echo "🌐 Веб-интерфейс: http://$(hostname -I | awk '{print $1}'):8080"
echo ""

