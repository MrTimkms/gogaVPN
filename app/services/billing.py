from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.models import User, Transaction, SystemSettings
from app.config import settings
from typing import List, Tuple


def get_subscription_price(db: Session) -> float:
    """Получает цену подписки из настроек"""
    setting = db.query(SystemSettings).filter(SystemSettings.key == "subscription_price").first()
    if setting:
        return float(setting.value)
    return settings.default_subscription_price


def set_subscription_price(db: Session, price: float):
    """Устанавливает цену подписки"""
    setting = db.query(SystemSettings).filter(SystemSettings.key == "subscription_price").first()
    if setting:
        setting.value = str(price)
    else:
        setting = SystemSettings(key="subscription_price", value=str(price))
        db.add(setting)
    db.commit()


def get_users_for_billing(db: Session, billing_date: date) -> List[User]:
    """Получает список пользователей, у которых сегодня день списания"""
    return db.query(User).filter(
        User.next_billing_date == billing_date,
        User.status != "blocked"
    ).all()


def process_billing(db: Session, user: User) -> Tuple[bool, str]:
    """
    Обрабатывает списание для пользователя
    Returns: (success, message)
    """
    price = get_subscription_price(db)
    
    if user.balance >= price:
        # Сценарий А: Денег хватает
        user.balance -= price
        
        # Создаем транзакцию
        transaction = Transaction(
            user_id=user.id,
            amount=-price,
            transaction_type="withdrawal",
            description=f"Ежемесячная оплата VPN подписки"
        )
        db.add(transaction)
        
        # Сдвигаем дату следующего списания на месяц
        next_date = user.next_billing_date
        if next_date.month == 12:
            next_date = date(next_date.year + 1, 1, next_date.day)
        else:
            next_date = date(next_date.year, next_date.month + 1, next_date.day)
        
        user.next_billing_date = next_date
        user.status = "active"
        
        db.commit()
        
        return True, f"✅ Оплата VPN прошла успешно. Доступ продлен до {next_date.strftime('%d.%m.%Y')}"
    
    else:
        # Сценарий Б: Денег мало
        user.status = "debt"
        db.commit()
        
        return False, f"❌ Недостаточно средств. Доступ будет приостановлен. Пополните баланс."


def get_debtors(db: Session) -> List[User]:
    """Получает список должников"""
    price = get_subscription_price(db)
    return db.query(User).filter(
        User.balance < price,
        User.status == "debt"
    ).all()


def check_upcoming_billing(db: Session, days_before: int = 2) -> List[User]:
    """Проверяет пользователей, у которых скоро списание и недостаточно средств"""
    today = date.today()
    check_date = today + timedelta(days=days_before)
    price = get_subscription_price(db)
    
    users = db.query(User).filter(
        User.next_billing_date == check_date,
        User.balance < price,
        User.status != "blocked"
    ).all()
    
    return users

