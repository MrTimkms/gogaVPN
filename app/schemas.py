from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime


# User Schemas
class UserBase(BaseModel):
    name: str
    telegram_id: Optional[int] = None
    balance: float = 0.0
    start_date: date
    next_billing_date: date
    status: str = "active"
    key_data: Optional[str] = None
    server_name: Optional[str] = None
    enable_billing_notifications: bool = True
    notify_before_billing_days: int = 2
    enable_negative_balance_notifications: bool = True


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    telegram_id: Optional[int] = None
    balance: Optional[float] = None
    start_date: Optional[date] = None
    next_billing_date: Optional[date] = None
    status: Optional[str] = None
    key_data: Optional[str] = None
    server_name: Optional[str] = None
    enable_billing_notifications: Optional[bool] = None
    notify_before_billing_days: Optional[int] = None
    enable_negative_balance_notifications: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    is_ghost: bool
    enable_billing_notifications: bool
    notify_before_billing_days: int
    enable_negative_balance_notifications: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Transaction Schemas
class TransactionCreate(BaseModel):
    user_id: int
    amount: float
    transaction_type: str
    description: Optional[str] = None


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    transaction_type: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# CSV Import Schema
class CSVImportResponse(BaseModel):
    imported: int
    errors: list
    ghost_users: int


# Admin Schemas
class BalanceAdjustment(BaseModel):
    user_id: int
    amount: float
    description: str


class KeyUpdate(BaseModel):
    user_id: int
    key_data: str
    server_name: Optional[str] = None


class UserMapping(BaseModel):
    ghost_user_id: int
    telegram_id: int


# Settings
class SettingsUpdate(BaseModel):
    subscription_price: float


class SBPInfoUpdate(BaseModel):
    phone: Optional[str] = None
    account: Optional[str] = None
    qr_code_path: Optional[str] = None


class SendNotificationRequest(BaseModel):
    user_id: int
    message: str

