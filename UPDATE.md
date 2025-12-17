# 🔄 Обновление проекта на VPS

## Быстрое обновление (рекомендуется)

Выполните на вашем VPS:

```bash
cd ~/gogaVPN
git pull
docker compose down
docker compose build --no-cache
docker compose up -d
```

Или одной командой:

```bash
cd ~/gogaVPN && git pull && docker compose down && docker compose build --no-cache && docker compose up -d
```

## Что происходит:

1. ✅ `git pull` - скачивает новые изменения из GitHub
2. ✅ `docker compose down` - останавливает контейнеры
3. ✅ `docker compose build --no-cache` - пересобирает образы с новым кодом
4. ✅ `docker compose up -d` - запускает обновленные контейнеры

## Проверка после обновления:

```bash
# Статус контейнеров
docker compose ps

# Логи (должны быть без ошибок)
docker compose logs -f
```

## Если что-то пошло не так:

```bash
# Откат к предыдущей версии
cd ~/gogaVPN
git reset --hard HEAD~1
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Автоматический скрипт обновления:

Создайте файл `update.sh`:

```bash
#!/bin/bash
cd ~/gogaVPN
echo "🔄 Обновление проекта..."
git pull
echo "✅ Код обновлен"
echo "🛑 Остановка контейнеров..."
docker compose down
echo "🔨 Пересборка..."
docker compose build --no-cache
echo "🚀 Запуск..."
docker compose up -d
echo "✅ Обновление завершено!"
docker compose ps
```

Затем запустите:
```bash
chmod +x update.sh
./update.sh
```

