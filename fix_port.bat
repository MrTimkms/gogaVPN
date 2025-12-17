@echo off
chcp 65001 >nul
echo 🔍 Проверка порта 8080...
echo.

REM Проверка через netstat
netstat -ano | findstr :8080
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ⚠️ Порт 8080 занят!
    echo.
) else (
    echo ✅ Порт 8080 свободен
    echo.
)

echo 💡 Решения:
echo 1. Остановить процесс, использующий порт 8080
echo 2. Изменить порт в docker-compose.yml на другой (например, 8081^)
echo.
set /p CHANGE_PORT="Хотите изменить порт на 8081? (y/n): "

if /i "!CHANGE_PORT!"=="y" (
    REM Создание резервной копии
    copy docker-compose.yml docker-compose.yml.bak >nul
    
    REM Замена порта через PowerShell
    powershell -Command "(Get-Content docker-compose.yml) -replace '\"8080:8000\"', '\"8081:8000\"' | Set-Content docker-compose.yml"
    
    echo.
    echo ✅ Порт изменен на 8081
    echo Теперь проект будет доступен по адресу: http://localhost:8081
    echo.
    echo Запустите снова: docker compose up -d
)

pause

