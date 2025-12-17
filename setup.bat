@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

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

REM Функция для генерации SECRET_KEY (упрощенная версия)
set SECRET_KEY=change-me-in-production-%RANDOM%-%RANDOM%

REM Создание или обновление .env файла
if not exist .env (
    echo 📝 Настройка конфигурации...
    echo.
    
    REM Запрос BOT_TOKEN
    echo 🤖 Telegram Bot Token
    echo    Получите у @BotFather в Telegram: https://t.me/BotFather
    echo    Команда: /newbot
    echo.
    set /p BOT_TOKEN="Введите BOT_TOKEN: "
    if "!BOT_TOKEN!"=="" (
        echo ❌ BOT_TOKEN не может быть пустым!
        pause
        exit /b 1
    )
    
    REM Запрос ADMIN_TELEGRAM_IDS
    echo.
    echo 👤 Telegram ID администратора
    echo    Получите у @userinfobot в Telegram: https://t.me/userinfobot
    echo    Команда: /start
    echo.
    set /p ADMIN_TELEGRAM_IDS="Введите ADMIN_TELEGRAM_IDS: "
    if "!ADMIN_TELEGRAM_IDS!"=="" (
        echo ❌ ADMIN_TELEGRAM_IDS не может быть пустым!
        pause
        exit /b 1
    )
    
    REM Запрос TELEGRAM_BOT_NAME
    echo.
    echo 📝 Имя бота (без символа @^)
    echo    Например: my_vpn_bot
    echo.
    set /p TELEGRAM_BOT_NAME="Введите TELEGRAM_BOT_NAME (или Enter для пропуска): "
    if "!TELEGRAM_BOT_NAME!"=="" set TELEGRAM_BOT_NAME=your_bot_username
    
    REM Создание .env файла
    (
        echo # Database (для Docker используется PostgreSQL из docker-compose^)
        echo DATABASE_URL=postgresql://vpn_user:vpn_password@db:5432/vpn_billing
        echo.
        echo # Telegram Bot
        echo BOT_TOKEN=!BOT_TOKEN!
        echo ADMIN_TELEGRAM_IDS=!ADMIN_TELEGRAM_IDS!
        echo.
        echo # Telegram Login Widget
        echo TELEGRAM_BOT_NAME=!TELEGRAM_BOT_NAME!
        echo.
        echo # Server
        echo SECRET_KEY=!SECRET_KEY!
        echo DEBUG=True
        echo.
        echo # Billing
        echo DEFAULT_SUBSCRIPTION_PRICE=100
    ) > .env
    
    echo.
    echo ✅ Файл .env создан и настроен!
    echo.
) else (
    echo ✅ Файл .env уже существует
    echo.
    set /p UPDATE_ENV="Хотите обновить настройки? (y/n): "
    if /i "!UPDATE_ENV!"=="y" (
        REM Запрос BOT_TOKEN
        echo.
        set /p NEW_BOT_TOKEN="Введите новый BOT_TOKEN (или Enter чтобы оставить текущий): "
        if not "!NEW_BOT_TOKEN!"=="" (
            powershell -Command "(Get-Content .env) -replace '^BOT_TOKEN=.*', 'BOT_TOKEN=!NEW_BOT_TOKEN!' | Set-Content .env"
        )
        
        REM Запрос ADMIN_TELEGRAM_IDS
        set /p NEW_ADMIN_IDS="Введите новый ADMIN_TELEGRAM_IDS (или Enter чтобы оставить текущий): "
        if not "!NEW_ADMIN_IDS!"=="" (
            powershell -Command "(Get-Content .env) -replace '^ADMIN_TELEGRAM_IDS=.*', 'ADMIN_TELEGRAM_IDS=!NEW_ADMIN_IDS!' | Set-Content .env"
        )
        
        REM Запрос TELEGRAM_BOT_NAME
        set /p NEW_BOT_NAME="Введите новый TELEGRAM_BOT_NAME (или Enter чтобы оставить текущий): "
        if not "!NEW_BOT_NAME!"=="" (
            powershell -Command "(Get-Content .env) -replace '^TELEGRAM_BOT_NAME=.*', 'TELEGRAM_BOT_NAME=!NEW_BOT_NAME!' | Set-Content .env"
        )
        
        echo ✅ Настройки обновлены!
    )
    echo.
)

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
echo    - Веб-интерфейс: http://localhost:8080
echo    - API документация: http://localhost:8080/docs
echo    - Админ-панель: http://localhost:8080/admin
echo.
echo 📊 Просмотр логов:
echo    docker compose logs -f
echo.
echo 🛑 Остановка:
echo    docker compose down
echo.

pause
