#!/bin/bash
set -e

echo "🚀 Запуск инициализации..."

# Ожидание готовности базы данных (если используется PostgreSQL)
if [ -n "$DATABASE_URL" ] && [[ "$DATABASE_URL" == postgresql* ]]; then
    echo "⏳ Ожидание подключения к базе данных..."
    max_attempts=30
    attempt=0
    until python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')" 2>/dev/null; do
        attempt=$((attempt + 1))
        if [ $attempt -ge $max_attempts ]; then
            echo "❌ База данных недоступна после $max_attempts попыток"
            exit 1
        fi
        echo "База данных недоступна - ожидание... ($attempt/$max_attempts)"
        sleep 2
    done
    echo "✅ База данных доступна"
fi

# Применение миграций
echo "📦 Применение миграций базы данных..."
alembic upgrade head 2>&1 || {
    echo "⚠️ Ошибка миграций, пробуем создать таблицы напрямую..."
    python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)" 2>&1 || echo "⚠️ Таблицы уже созданы"
}

echo "✅ Инициализация завершена!"

# Запуск команды
exec "$@"
