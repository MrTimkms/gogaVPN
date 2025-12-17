# 🚀 Развертывание на VPS сервере через Docker

## 📋 Что нужно

- VPS сервер (Ubuntu/Debian)
- Доступ по SSH
- Домен (опционально, но рекомендуется)

## 🔧 Шаг 1: Подключение к VPS

```bash
ssh root@ваш_сервер_ip
# или
ssh username@ваш_сервер_ip
```

## 🐳 Шаг 2: Установка Docker на VPS

### Для Ubuntu/Debian:

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo apt install docker-compose-plugin -y

# Добавление пользователя в группу docker (чтобы не писать sudo)
sudo usermod -aG docker $USER

# Перезагрузка сессии (или выйдите и войдите заново)
newgrp docker

# Проверка установки
docker --version
docker compose version
```

## 📥 Шаг 3: Клонирование проекта на VPS

```bash
# Переход в домашнюю директорию
cd ~

# Клонирование проекта
git clone https://github.com/MrTimkms/gogaVPN.git
# или если используете gh:
gh repo clone MrTimkms/gogaVPN

cd gogaVPN
```

## ⚙️ Шаг 4: Настройка проекта

### Вариант А: Автоматическая настройка (рекомендуется)

```bash
# Сделать скрипт исполняемым
chmod +x setup.sh

# Запустить установку
./setup.sh
```

Скрипт запросит:
- BOT_TOKEN
- ADMIN_TELEGRAM_IDS
- TELEGRAM_BOT_NAME

### Вариант Б: Ручная настройка

```bash
# Создать .env файл
cp env.example.txt .env

# Отредактировать .env
nano .env
```

Заполните:
```env
DATABASE_URL=postgresql://vpn_user:vpn_password@db:5432/vpn_billing
BOT_TOKEN=ваш_токен_бота
ADMIN_TELEGRAM_IDS=ваш_telegram_id
TELEGRAM_BOT_NAME=имя_вашего_бота
SECRET_KEY=сгенерируйте_случайный_ключ
DEBUG=False
DEFAULT_SUBSCRIPTION_PRICE=100
```

## 🚀 Шаг 5: Запуск проекта

```bash
# Запуск всех контейнеров
docker compose up -d --build

# Проверка статуса
docker compose ps

# Просмотр логов
docker compose logs -f
```

## 🌐 Шаг 6: Настройка Nginx (для доступа по домену)

### Установка Nginx

```bash
sudo apt install nginx -y
```

### Создание конфигурации

```bash
sudo nano /etc/nginx/sites-available/vpn-billing
```

Вставьте (замените `your-domain.com` на ваш домен):

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Таймауты для долгих запросов
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### Активация конфигурации

```bash
# Создать символическую ссылку
sudo ln -s /etc/nginx/sites-available/vpn-billing /etc/nginx/sites-enabled/

# Проверить конфигурацию
sudo nginx -t

# Перезапустить Nginx
sudo systemctl restart nginx
```

## 🔒 Шаг 7: Настройка SSL (Let's Encrypt)

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx -y

# Получение SSL сертификата
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Автоматическое обновление (настроено автоматически)
```

## 🔥 Шаг 8: Настройка Firewall

```bash
# Установка UFW (если не установлен)
sudo apt install ufw -y

# Разрешить SSH
sudo ufw allow 22/tcp

# Разрешить HTTP и HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Включить firewall
sudo ufw enable

# Проверка статуса
sudo ufw status
```

## ✅ Проверка работы

1. **Веб-интерфейс**: http://your-domain.com или http://ваш_ip:8000
2. **API документация**: http://your-domain.com/docs
3. **Админ-панель**: http://your-domain.com/admin
4. **Telegram бот**: Отправьте `/start` вашему боту

## 📊 Полезные команды

### Просмотр логов
```bash
# Все сервисы
docker compose logs -f

# Только бот
docker compose logs -f bot

# Только API
docker compose logs -f backend

# Только база данных
docker compose logs -f db
```

### Перезапуск
```bash
docker compose restart
```

### Остановка
```bash
docker compose down
```

### Обновление проекта
```bash
cd ~/gogaVPN
git pull
docker compose up -d --build
```

### Резервное копирование базы данных
```bash
# Создать бэкап
docker compose exec db pg_dump -U vpn_user vpn_billing > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановить из бэкапа
docker compose exec -T db psql -U vpn_user vpn_billing < backup_20240101_120000.sql
```

## 🔄 Автозапуск при перезагрузке сервера

Docker Compose автоматически запускает контейнеры при перезагрузке (благодаря `restart: unless-stopped` в docker-compose.yml).

Для проверки:
```bash
# Перезагрузить сервер
sudo reboot

# После перезагрузки проверить
docker compose ps
```

## 🛡️ Дополнительная безопасность

### Изменение пароля PostgreSQL

1. Отредактируйте `docker-compose.yml`:
```yaml
POSTGRES_PASSWORD: ваш_новый_сложный_пароль
```

2. Обновите `.env`:
```env
DATABASE_URL=postgresql://vpn_user:ваш_новый_сложный_пароль@db:5432/vpn_billing
```

3. Пересоздайте контейнеры:
```bash
docker compose down -v
docker compose up -d --build
```

### Настройка fail2ban (защита от брутфорса)

```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## 📝 Структура файлов на сервере

```
~/gogaVPN/
├── .env                 # Ваши настройки (НЕ коммитьте в git!)
├── docker-compose.yml   # Конфигурация Docker
├── Dockerfile          # Образ приложения
└── ...                 # Остальные файлы проекта
```

## ❓ Решение проблем

### Порт 8000 занят

**Ошибка:** `failed to bind host port 0.0.0.0:8000/tcp: address already in use`

**Решение 1: Найти и остановить процесс**
```bash
# Проверить, что использует порт
sudo lsof -i :8000
# или
sudo netstat -tulpn | grep :8000

# Остановить процесс (замените PID на номер процесса)
sudo kill -9 PID
```

**Решение 2: Изменить порт (быстрое решение)**

Используйте скрипт:
```bash
chmod +x fix_port.sh
./fix_port.sh
```

Или вручную отредактируйте `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Внешний:Внутренний (теперь доступ по порту 8001)
```

После изменения:
```bash
docker compose up -d
```

Проект будет доступен по адресу: `http://ваш_сервер_ip:8001`

### Бот не отвечает
```bash
# Проверить логи
docker compose logs bot

# Проверить .env файл
cat .env | grep BOT_TOKEN
```

### База данных не подключается
```bash
# Проверить статус контейнера БД
docker compose ps db

# Проверить логи БД
docker compose logs db

# Подождать 10-15 секунд после запуска (БД инициализируется)
```

### Nginx не работает
```bash
# Проверить статус
sudo systemctl status nginx

# Проверить конфигурацию
sudo nginx -t

# Перезапустить
sudo systemctl restart nginx
```

## 🎉 Готово!

Ваш проект развернут на VPS и доступен по домену или IP адресу!

