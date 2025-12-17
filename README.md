# Система биллинга и управления клиентами VPN-сервиса

Комплексная система для управления VPN-сервисом, включающая Telegram-бот и веб-сайт.

## Технологии

- **Backend:** FastAPI
- **Telegram Bot:** aiogram 3.x
- **База данных:** PostgreSQL (или SQLite для разработки)
- **Планировщик:** APScheduler
- **Frontend:** HTML/JS с Bootstrap

## Быстрый старт

### 1. Клонирование и установка зависимостей

```bash
git clone <repository>
cd ТГБотVPN
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Настройка окружения

Скопируйте `.env.example` в `.env` и заполните необходимые параметры:

```bash
cp .env.example .env
```

Обязательно укажите:
- `BOT_TOKEN` - токен вашего Telegram-бота
- `ADMIN_TELEGRAM_IDS` - ID администраторов через запятую
- `DATABASE_URL` - строка подключения к БД

### 3. Инициализация базы данных

```bash
python -m alembic upgrade head
```

### 4. Запуск через Docker Compose (рекомендуется)

```bash
docker-compose up -d
```

### 5. Запуск вручную

В разных терминалах:

```bash
# Backend API
uvicorn app.main:app --reload --port 8000

# Telegram Bot
python -m app.bot.main

# Планировщик (запускается автоматически с ботом)
```

## Структура проекта

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI приложение
│   ├── config.py           # Конфигурация
│   ├── database.py         # Подключение к БД
│   ├── models.py           # SQLAlchemy модели
│   ├── schemas.py          # Pydantic схемы
│   ├── api/                # API эндпоинты
│   │   ├── __init__.py
│   │   ├── users.py
│   │   ├── admin.py
│   │   └── auth.py
│   ├── bot/                # Telegram бот
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── handlers.py
│   │   └── keyboards.py
│   ├── services/           # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── billing.py
│   │   ├── notifications.py
│   │   └── csv_import.py
│   └── scheduler.py        # Планировщик задач
├── static/                 # Статические файлы
│   ├── css/
│   ├── js/
│   └── uploads/
├── templates/              # HTML шаблоны
│   ├── index.html
│   ├── admin.html
│   └── login.html
├── alembic/                # Миграции БД
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Основные функции

### Для пользователей:
- Просмотр баланса и статуса подписки
- Получение VPN-ключей
- Пополнение баланса
- Уведомления о списаниях

### Для администраторов:
- Импорт пользователей из CSV
- Управление балансом
- Загрузка VPN-ключей
- Мониторинг должников
- Настройка тарифов

## Документация API

После запуска сервера доступна по адресу: `http://localhost:8000/docs`

## Лицензия

MIT

