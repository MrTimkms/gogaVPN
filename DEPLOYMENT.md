# Инструкция по развертыванию

> **Для быстрого развертывания на VPS через Docker см. [VPS_DEPLOYMENT.md](VPS_DEPLOYMENT.md)**

## Развертывание на Ubuntu/Debian сервере

### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y python3.11 python3.11-venv python3-pip postgresql postgresql-contrib git docker.io docker-compose

# Запуск PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Клонирование проекта

```bash
cd /opt
sudo git clone <your-repository-url> vpn-billing
cd vpn-billing
sudo chown -R $USER:$USER .
```

### 3. Настройка окружения

```bash
# Создание виртуального окружения
python3.11 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 4. Настройка базы данных PostgreSQL

```bash
# Вход в PostgreSQL
sudo -u postgres psql

# Создание базы данных и пользователя
CREATE DATABASE vpn_billing;
CREATE USER vpn_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE vpn_billing TO vpn_user;
\q
```

### 5. Настройка переменных окружения

```bash
# Копирование примера
cp .env.example .env

# Редактирование .env
nano .env
```

Заполните следующие параметры:

```env
DATABASE_URL=postgresql://vpn_user:your_secure_password@localhost:5432/vpn_billing
BOT_TOKEN=your_telegram_bot_token
ADMIN_TELEGRAM_IDS=123456789,987654321
TELEGRAM_BOT_NAME=your_bot_username
SECRET_KEY=your-secret-key-here
DEBUG=False
DEFAULT_SUBSCRIPTION_PRICE=100
```

### 6. Инициализация базы данных

```bash
# Активация виртуального окружения
source venv/bin/activate

# Создание миграций (если нужно)
alembic revision --autogenerate -m "Initial migration"

# Применение миграций
alembic upgrade head

# Инициализация тестовых данных (опционально)
python scripts/init_db.py
```

### 7. Развертывание через Docker Compose (рекомендуется)

```bash
# Редактирование docker-compose.yml (убедитесь, что переменные окружения указаны)
# Запуск контейнеров
docker-compose up -d

# Просмотр логов
docker-compose logs -f
```

### 8. Развертывание без Docker

#### Запуск Backend API

Создайте systemd service:

```bash
sudo nano /etc/systemd/system/vpn-billing-api.service
```

Содержимое:

```ini
[Unit]
Description=VPN Billing API
After=network.target postgresql.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/opt/vpn-billing
Environment="PATH=/opt/vpn-billing/venv/bin"
ExecStart=/opt/vpn-billing/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Запуск Telegram Bot

```bash
sudo nano /etc/systemd/system/vpn-billing-bot.service
```

Содержимое:

```ini
[Unit]
Description=VPN Billing Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/opt/vpn-billing
Environment="PATH=/opt/vpn-billing/venv/bin"
ExecStart=/opt/vpn-billing/venv/bin/python -m app.bot.main
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Запуск сервисов

```bash
sudo systemctl daemon-reload
sudo systemctl enable vpn-billing-api
sudo systemctl enable vpn-billing-bot
sudo systemctl start vpn-billing-api
sudo systemctl start vpn-billing-bot

# Проверка статуса
sudo systemctl status vpn-billing-api
sudo systemctl status vpn-billing-bot
```

### 9. Настройка Nginx (опционально, для веб-интерфейса)

```bash
sudo apt install nginx

sudo nano /etc/nginx/sites-available/vpn-billing
```

Конфигурация:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/vpn-billing /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 10. Настройка SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 11. Проверка работы

1. **API**: Откройте `http://your-server-ip:8000/docs` - должна открыться документация Swagger
2. **Веб-интерфейс**: Откройте `http://your-server-ip:8000` или `http://your-domain.com`
3. **Бот**: Отправьте `/start` в Telegram боту

### 12. Резервное копирование

Создайте скрипт для резервного копирования БД:

```bash
#!/bin/bash
BACKUP_DIR="/backups/vpn-billing"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
pg_dump -U vpn_user vpn_billing > $BACKUP_DIR/backup_$DATE.sql
# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "backup_*.sql" -mtime +30 -delete
```

Добавьте в crontab:

```bash
0 2 * * * /path/to/backup-script.sh
```

## Обновление системы

```bash
cd /opt/vpn-billing
git pull
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart vpn-billing-api
sudo systemctl restart vpn-billing-bot
```

## Мониторинг

Проверка логов:

```bash
# API
sudo journalctl -u vpn-billing-api -f

# Bot
sudo journalctl -u vpn-billing-bot -f

# Docker
docker-compose logs -f
```

## Устранение неполадок

1. **Бот не отвечает**: Проверьте `BOT_TOKEN` в `.env`
2. **Ошибки подключения к БД**: Проверьте `DATABASE_URL` и доступность PostgreSQL
3. **Планировщик не работает**: Убедитесь, что бот запущен (планировщик запускается вместе с ботом)

