@echo off
chcp 65001 >nul
echo 🔍 Проверка статуса VPN Billing System
echo ========================================
echo.

echo 1️⃣ Проверка Docker...
where docker >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=*" %%i in ('docker --version') do echo    ✅ Docker установлен: %%i
) else (
    echo    ❌ Docker не установлен
    pause
    exit /b 1
)
echo.

echo 2️⃣ Проверка контейнеров...
docker compose ps
echo.

echo 3️⃣ Проверка портов...
netstat -ano | findstr ":8000 :8001"
if %ERRORLEVEL% EQU 0 (
    echo    ✅ Порт открыт
) else (
    echo    ⚠️ Порт не найден
)
echo.

echo 4️⃣ Проверка веб-интерфейса...
curl -s -o nul -w "%%{http_code}" http://localhost:8000 >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo    ✅ Веб-интерфейс доступен
) else (
    curl -s -o nul -w "%%{http_code}" http://localhost:8001 >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo    ✅ Веб-интерфейс доступен на порту 8001
    ) else (
        echo    ⚠️ Веб-интерфейс недоступен
    )
)
echo.

echo 5️⃣ Проверка логов (последние 5 строк)...
echo    Backend:
docker compose logs --tail=5 backend 2>nul
echo.
echo    Bot:
docker compose logs --tail=5 bot 2>nul
echo.

echo 6️⃣ Проверка конфигурации...
if exist .env (
    echo    ✅ Файл .env существует
    findstr /C:"BOT_TOKEN=" .env | findstr /V "your_telegram_bot_token_here" >nul
    if %ERRORLEVEL% EQU 0 (
        echo    ✅ BOT_TOKEN настроен
    ) else (
        echo    ⚠️ BOT_TOKEN не настроен
    )
) else (
    echo    ❌ Файл .env не найден
)
echo.

echo 📋 Итоговая информация:
echo ==========================
echo.
echo 🌐 Веб-интерфейс:
echo    http://localhost:8000 (или 8001^)
echo.
echo 📚 API документация:
echo    http://localhost:8000/docs (или 8001^)
echo.
echo ⚙️ Админ-панель:
echo    http://localhost:8000/admin (или 8001^)
echo.

pause

