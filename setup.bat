@echo off
chcp 65001 >nul
echo 🔧 Настройка проекта VPN Billing System
echo ========================================
echo.

REM Проверка наличия Docker
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker не установлен!
    echo Установите Docker: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

echo ✅ Docker найден
echo.

REM Создание .env файла если его нет
if not exist .env (
    echo 📝 Создание файла .env...
    
    if exist env.example.txt (
        copy env.example.txt .env >nul
    ) else (
        (
            echo # Database (для Docker используется PostgreSQL из docker-compose^)
            echo DATABASE_URL=postgresql://vpn_user:vpn_password@db:5432/vpn_billing
            echo.
            echo # Telegram Bot
            echo BOT_TOKEN=your_telegram_bot_token_here
            echo ADMIN_TELEGRAM_IDS=123456789
            echo.
            echo # Telegram Login Widget
            echo TELEGRAM_BOT_NAME=your_bot_username
            echo.
            echo # Server
            echo SECRET_KEY=change-me-in-production
            echo DEBUG=True
            echo.
            echo # Billing
            echo DEFAULT_SUBSCRIPTION_PRICE=100
        ) > .env
    )
    
    echo ✅ Файл .env создан
    echo.
    echo ⚠️  ВАЖНО: Отредактируйте файл .env и укажите:
    echo    - BOT_TOKEN (получите у @BotFather в Telegram^)
    echo    - ADMIN_TELEGRAM_IDS (ваш Telegram ID^)
    echo    - TELEGRAM_BOT_NAME (имя вашего бота без @^)
    echo.
    pause
) else (
    echo ✅ Файл .env уже существует
)

echo.
echo 🐳 Запуск Docker контейнеров...
echo.

REM Запуск через docker compose
docker compose up -d --build

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Ошибка запуска Docker!
    echo Попробуйте: docker-compose up -d --build
    pause
    exit /b 1
)

echo.
echo ⏳ Ожидание запуска сервисов...
timeout /t 5 /nobreak >nul

echo.
echo ✅ Проект запущен!
echo.
echo 📋 Доступные сервисы:
echo    - Веб-интерфейс: http://localhost:8000
echo    - API документация: http://localhost:8000/docs
echo    - Админ-панель: http://localhost:8000/admin
echo.
echo 📊 Просмотр логов:
echo    docker compose logs -f
echo.
echo 🛑 Остановка:
echo    docker compose down
echo.

pause

