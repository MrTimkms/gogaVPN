# Безопасное обновление без потери данных БД

## Команды для обновления на сервере:

```bash
# 1. Перейти в директорию проекта
cd ~/gogaVPN

# 2. Получить последние изменения из GitHub
git pull

# 3. Остановить только контейнеры приложения (БД НЕ трогаем!)
docker compose stop backend bot

# 4. Пересобрать образы приложения
docker compose build backend bot

# 5. Запустить контейнеры заново
docker compose up -d

# 6. Проверить статус
docker compose ps

# 7. Проверить логи (опционально)
docker compose logs -f bot
```

## Альтернативный вариант (если первый не работает):

```bash
cd ~/gogaVPN
git pull
docker compose down  # Останавливает контейнеры, НО НЕ удаляет volumes!
docker compose build --no-cache backend bot
docker compose up -d
docker compose ps
```

## Важно:
- `docker compose down` НЕ удаляет volumes (данные БД сохраняются)
- `docker compose down -v` - ЭТО удалит volumes! НЕ используйте флаг `-v`!
- База данных в volume `postgres_data` останется нетронутой

## Если что-то пошло не так:

```bash
# Проверить, что volume существует
docker volume ls | grep postgres_data

# Проверить логи
docker compose logs db
docker compose logs backend
docker compose logs bot
```

