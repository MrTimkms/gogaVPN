from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
from app.database import Base


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=True, index=True)
    name = Column(String(255), nullable=False)
    balance = Column(Float, default=0.0)
    start_date = Column(Date, nullable=False)  # Дата начала подписки
    next_billing_date = Column(Date, nullable=False)  # Дата следующего списания
    status = Column(String(50), default="active")  # active, blocked, debt
    key_data = Column(Text, nullable=True)  # VPN ключ
    server_name = Column(String(100), nullable=True)  # Сервер 1, 2 или 3
    is_ghost = Column(Boolean, default=False)  # Спящий профиль без telegram_id
    # Настройки уведомлений
    enable_billing_notifications = Column(Boolean, default=True)  # Включены ли уведомления о списании
    notify_before_billing_days = Column(Integer, default=2)  # За сколько дней до списания уведомлять
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Связи
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Transaction(Base):
    """Модель транзакции (пополнение/списание)"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)  # Может быть отрицательным для списаний
    transaction_type = Column(String(50), nullable=False)  # deposit, withdrawal, adjustment
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="transactions")


class Notification(Base):
    """Модель уведомлений"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # billing, balance, key_update, reminder
    sent = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="notifications")


class SystemSettings(Base):
    """Настройки системы"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

