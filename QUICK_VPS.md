# ⚡ Быстрое развертывание на VPS (5 минут)

## 🎯 Что нужно сделать:

### 1. Подключитесь к VPS
```bash
ssh root@ваш_сервер_ip
```

### 2. Установите Docker (одна команда)
```bash
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh && sudo apt install docker-compose-plugin -y
```

### 3. Клонируйте проект
```bash
cd ~ && git clone https://github.com/MrTimkms/gogaVPN.git && cd gogaVPN
```

### 4. Запустите установку
```bash
chmod +x setup.sh && ./setup.sh
```

Введите:
- BOT_TOKEN (от @BotFather)
- ADMIN_TELEGRAM_IDS (от @userinfobot)
- TELEGRAM_BOT_NAME (опционально)

### 5. Готово! 

Откройте: **http://ваш_сервер_ip:8000**

---

## 🌐 Если есть домен (опционально)

### Установите Nginx
```bash
sudo apt install nginx -y
```

### Создайте конфиг
```bash
sudo nano /etc/nginx/sites-available/vpn-billing
```

Вставьте (замените `your-domain.com`):
```nginx
server {
    listen 80;
    server_name your-domain.com;
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Активация
```bash
sudo ln -s /etc/nginx/sites-available/vpn-billing /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
```

### SSL (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

## 📊 Полезные команды

```bash
# Проверка статуса (все компоненты)
chmod +x check_status.sh && ./check_status.sh

# Логи
docker compose logs -f

# Перезапуск
docker compose restart

# Остановка
docker compose down

# Обновление
git pull && docker compose up -d --build
```

## ✅ Как проверить, что всё работает?

### Быстрая проверка:
```bash
# Статус контейнеров
docker compose ps

# Все должны быть "Up" и "healthy"
```

### Полная проверка:
```bash
chmod +x check_status.sh
./check_status.sh
```

Скрипт проверит:
- ✅ Docker установлен
- ✅ Контейнеры запущены
- ✅ Порт открыт
- ✅ Веб-интерфейс доступен
- ✅ Конфигурация настроена

---

**Подробная инструкция**: [VPS_DEPLOYMENT.md](VPS_DEPLOYMENT.md)

## 🔄 Переустановка

Если нужно переустановить всё заново:

```bash
# Быстрая переустановка (сохраняет данные)
cd ~/gogaVPN && git pull && docker compose down && docker compose build --no-cache && docker compose up -d

# Полная переустановка (удаляет всё)
chmod +x reinstall.sh && ./reinstall.sh

# Установка с нуля
chmod +x fresh_install.sh && ./fresh_install.sh
```

**Подробнее**: [REINSTALL.md](REINSTALL.md)

