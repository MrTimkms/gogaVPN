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
    """Получает список должников (пользователи с отрицательным балансом или балансом меньше цены подписки)"""
    price = get_subscription_price(db)
    return db.query(User).filter(
        User.balance < price,
        User.is_ghost == False  # Исключаем спящие профили
    ).order_by(User.balance.asc()).all()  # Сортируем по балансу (от меньшего к большему)


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


def get_sbp_info(db: Session) -> dict:
    """Получает информацию о СБП для оплаты"""
    settings = {
        'phone': None,
        'account': None,
        'qr_code_path': None
    }
    
    phone_setting = db.query(SystemSettings).filter(SystemSettings.key == "sbp_phone").first()
    if phone_setting:
        settings['phone'] = phone_setting.value
    
    account_setting = db.query(SystemSettings).filter(SystemSettings.key == "sbp_account").first()
    if account_setting:
        settings['account'] = account_setting.value
    
    qr_setting = db.query(SystemSettings).filter(SystemSettings.key == "sbp_qr_code_path").first()
    if qr_setting:
        settings['qr_code_path'] = qr_setting.value
    
    return settings


def set_sbp_info(db: Session, phone: str = None, account: str = None, qr_code_path: str = None):
    """Устанавливает информацию о СБП"""
    if phone:
        setting = db.query(SystemSettings).filter(SystemSettings.key == "sbp_phone").first()
        if setting:
            setting.value = phone
        else:
            setting = SystemSettings(key="sbp_phone", value=phone)
            db.add(setting)
    
    if account:
        setting = db.query(SystemSettings).filter(SystemSettings.key == "sbp_account").first()
        if setting:
            setting.value = account
        else:
            setting = SystemSettings(key="sbp_account", value=account)
            db.add(setting)
    
    if qr_code_path:
        setting = db.query(SystemSettings).filter(SystemSettings.key == "sbp_qr_code_path").first()
        if setting:
            setting.value = qr_code_path
        else:
            setting = SystemSettings(key="sbp_qr_code_path", value=qr_code_path)
            db.add(setting)
    
    db.commit()

