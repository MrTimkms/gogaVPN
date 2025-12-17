from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserResponse
from typing import Optional

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/user/{telegram_id}", response_model=UserResponse)
def get_user_by_telegram_id(telegram_id: int, db: Session = Depends(get_db)):
    """Получает пользователя по telegram_id (для Telegram Login Widget)"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/verify")
def verify_telegram_auth(
    id: int,
    first_name: str,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
    photo_url: Optional[str] = None,
    auth_date: int = None,
    hash: str = None,
    db: Session = Depends(get_db)
):
    """
    Верификация Telegram авторизации
    В реальном проекте здесь должна быть проверка hash
    """
    user = db.query(User).filter(User.telegram_id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Обновляем имя, если изменилось
    if first_name:
        user.name = first_name + (f" {last_name}" if last_name else "")
        db.commit()
    
    return {"success": True, "user_id": user.id}

