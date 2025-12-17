from sqlalchemy.orm import Session
from app.models import Notification, User
from typing import Optional


def create_notification(
    db: Session,
    user_id: int,
    message: str,
    notification_type: str
) -> Notification:
    """Создает уведомление в базе"""
    notification = Notification(
        user_id=user_id,
        message=message,
        notification_type=notification_type,
        sent=False
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def mark_notification_sent(db: Session, notification_id: int):
    """Отмечает уведомление как отправленное"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification:
        notification.sent = True
        db.commit()


def get_pending_notifications(db: Session, user_id: Optional[int] = None) -> list:
    """Получает неотправленные уведомления"""
    query = db.query(Notification).filter(Notification.sent == False)
    if user_id:
        query = query.filter(Notification.user_id == user_id)
    return query.all()

