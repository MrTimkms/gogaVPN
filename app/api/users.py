from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Transaction
from app.schemas import UserResponse, TransactionResponse
from typing import List

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me/{telegram_id}", response_model=UserResponse)
def get_my_profile(telegram_id: int, db: Session = Depends(get_db)):
    """Получает профиль пользователя"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me/{telegram_id}/is-admin")
def check_is_admin(telegram_id: int):
    """Проверяет, является ли пользователь администратором"""
    from app.config import settings
    return {"is_admin": telegram_id in settings.admin_ids_list}


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Получает пользователя по ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}/transactions", response_model=List[TransactionResponse])
def get_user_transactions(user_id: int, db: Session = Depends(get_db)):
    """Получает транзакции пользователя"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).order_by(Transaction.created_at.desc()).limit(50).all()
    
    return transactions

