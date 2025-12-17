@echo off
chcp 65001 >nul
echo 🔍 Проверка порта 8000...
echo.

REM Проверка через netstat
netstat -ano | findstr :8000
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ⚠️ Порт 8000 занят!
    echo.
) else (
    echo ✅ Порт 8000 свободен
    echo.
)

echo 💡 Решения:
echo 1. Остановить процесс, использующий порт 8000
echo 2. Изменить порт в docker-compose.yml на другой (например, 8001^)
echo.
set /p CHANGE_PORT="Хотите изменить порт на 8001? (y/n): "

if /i "!CHANGE_PORT!"=="y" (
    REM Создание резервной копии
    copy docker-compose.yml docker-compose.yml.bak >nul
    
    REM Замена порта через PowerShell
    powershell -Command "(Get-Content docker-compose.yml) -replace '\"8000:8000\"', '\"8001:8000\"' | Set-Content docker-compose.yml"
    
    echo.
    echo ✅ Порт изменен на 8001
    echo Теперь проект будет доступен по адресу: http://localhost:8001
    echo.
    echo Запустите снова: docker compose up -d
)

pause

