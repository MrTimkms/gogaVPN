"""
Скрипт для инициализации базы данных с тестовыми данными
"""
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import User, SystemSettings
from app.services.billing import set_subscription_price
from datetime import date, timedelta

# Создаем таблицы
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # Устанавливаем цену подписки
    set_subscription_price(db, 100.0)
    print("✓ Цена подписки установлена: 100 ₽/мес")
    
    # Создаем тестовых пользователей
    test_users = [
        {
            "name": "Иван Иванов",
            "telegram_id": 123456789,
            "balance": 250.0,
            "start_date": date.today() - timedelta(days=15),
            "next_billing_date": date.today() + timedelta(days=15),
            "status": "active",
            "key_data": "vless://test-key-1@server1.example.com:443?security=tls&sni=server1.example.com#TestUser1",
            "server_name": "Сервер 1",
            "is_ghost": False
        },
        {
            "name": "Мария Петрова",
            "telegram_id": 987654321,
            "balance": 50.0,
            "start_date": date.today() - timedelta(days=10),
            "next_billing_date": date.today() + timedelta(days=20),
            "status": "active",
            "key_data": "vless://test-key-2@server2.example.com:443?security=tls&sni=server2.example.com#TestUser2",
            "server_name": "Сервер 2",
            "is_ghost": False
        },
        {
            "name": "Петр Сидоров",
            "telegram_id": None,
            "balance": 150.0,
            "start_date": date.today() - timedelta(days=5),
            "next_billing_date": date.today() + timedelta(days=25),
            "status": "active",
            "key_data": None,
            "server_name": None,
            "is_ghost": True  # Спящий профиль
        },
        {
            "name": "Анна Козлова",
            "telegram_id": 555666777,
            "balance": 30.0,
            "start_date": date.today() - timedelta(days=20),
            "next_billing_date": date.today(),  # Сегодня день списания
            "status": "debt",
            "key_data": "vless://test-key-4@server3.example.com:443?security=tls&sni=server3.example.com#TestUser4",
            "server_name": "Сервер 3",
            "is_ghost": False
        }
    ]
    
    for user_data in test_users:
        # Проверяем, существует ли пользователь
        if user_data["telegram_id"]:
            existing = db.query(User).filter(User.telegram_id == user_data["telegram_id"]).first()
        else:
            existing = None
        
        if not existing:
            user = User(**user_data)
            db.add(user)
            print(f"✓ Создан пользователь: {user_data['name']}")
        else:
            print(f"⊘ Пользователь уже существует: {user_data['name']}")
    
    db.commit()
    print("\n✓ База данных инициализирована успешно!")
    print(f"✓ Создано пользователей: {len(test_users)}")
    
except Exception as e:
    db.rollback()
    print(f"✗ Ошибка инициализации: {e}")
    raise
finally:
    db.close()

