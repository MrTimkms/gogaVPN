import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, Notification
from app.services.billing import (
    get_users_for_billing,
    process_billing,
    check_upcoming_billing,
    get_subscription_price
)
from app.services.notifications import create_notification, mark_notification_sent
from app.config import settings
from aiogram import Bot
from typing import Optional

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def send_notification(bot: Bot, telegram_id: int, message: str):
    """Отправляет уведомление пользователю"""
    try:
        await bot.send_message(telegram_id, message)
        logger.info(f"Уведомление отправлено пользователю {telegram_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления пользователю {telegram_id}: {e}")


async def daily_billing(bot: Bot):
    """Ежедневное списание средств"""
    logger.info("Запуск ежедневного биллинга")
    db = SessionLocal()
    try:
        today = date.today()
        users = get_users_for_billing(db, today)
        
        logger.info(f"Найдено {len(users)} пользователей для списания")
        
        for user in users:
            success, message = process_billing(db, user)
            
            # Отправляем уведомление пользователю
            if user.telegram_id:
                await send_notification(bot, user.telegram_id, message)
            
            # Уведомляем пользователя об отрицательном балансе, если настройка включена
            if not success and user.telegram_id and user.enable_negative_balance_notifications:
                negative_balance_message = (
                    f"⚠️ Ваш баланс отрицательный или недостаточен для оплаты подписки. "
                    f"Текущий баланс: {user.balance:.2f} ₽. "
                    f"Пожалуйста, пополните баланс для продолжения работы VPN."
                )
                await send_notification(bot, user.telegram_id, negative_balance_message)
            
            # Уведомляем админов о должниках
            if not success and user.telegram_id:
                admin_message = (
                    f"⚠️ Должник: @{user.telegram_id} ({user.name}). "
                    f"Оплата не прошла. Необходимо отключить ключ вручную!"
                )
                for admin_id in settings.admin_ids_list:
                    await send_notification(bot, admin_id, admin_message)
    finally:
        db.close()


async def check_upcoming_billings(bot: Bot):
    """Проверка предстоящих списаний (за 2 дня)"""
    logger.info("Проверка предстоящих списаний")
    db = SessionLocal()
    try:
        price = get_subscription_price(db)
        users = check_upcoming_billing(db, days_before=2)
        
        for user in users:
            # Проверяем настройку уведомлений пользователя
            if user.telegram_id and user.enable_billing_notifications:
                # Используем настройку пользователя для количества дней
                days_before = user.notify_before_billing_days if user.notify_before_billing_days else 2
                message = (
                    f"⏰ Напоминание: через {days_before} дн. списание {price:.2f} ₽, "
                    f"на счету не хватает средств. Текущий баланс: {user.balance:.2f} ₽"
                )
                await send_notification(bot, user.telegram_id, message)
    finally:
        db.close()


async def send_pending_notifications(bot: Bot):
    """Отправка неотправленных уведомлений"""
    db = SessionLocal()
    try:
        from app.services.notifications import get_pending_notifications
        notifications = get_pending_notifications(db)
        
        for notification in notifications:
            user = db.query(User).filter(User.id == notification.user_id).first()
            if user and user.telegram_id:
                try:
                    await send_notification(bot, user.telegram_id, notification.message)
                    mark_notification_sent(db, notification.id)
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления {notification.id}: {e}")
    finally:
        db.close()


def start_scheduler(bot: Bot):
    """Запускает планировщик задач"""
    # Ежедневное списание в 10:00
    scheduler.add_job(
        daily_billing,
        CronTrigger(hour=10, minute=0),
        args=[bot],
        id="daily_billing",
        replace_existing=True
    )
    
    # Проверка предстоящих списаний в 10:00
    scheduler.add_job(
        check_upcoming_billings,
        CronTrigger(hour=10, minute=0),
        args=[bot],
        id="check_upcoming",
        replace_existing=True
    )
    
    # Отправка уведомлений каждые 5 минут
    scheduler.add_job(
        send_pending_notifications,
        CronTrigger(minute="*/5"),
        args=[bot],
        id="send_notifications",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Планировщик задач настроен и запущен")

