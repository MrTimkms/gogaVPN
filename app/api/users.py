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


@router.get("/sbp-info")
def get_sbp_info_for_users(db: Session = Depends(get_db)):
    """Получает информацию о СБП для пользователей"""
    from app.services.billing import get_sbp_info
    sbp_info = get_sbp_info(db)
    
    # Если есть QR-код, формируем URL для доступа к нему
    qr_code_url = None
    if sbp_info.get('qr_code_path'):
        import os
        qr_path = sbp_info['qr_code_path']
        
        # Нормализуем путь
        if os.path.isabs(qr_path):
            # Для абсолютного пути извлекаем часть после 'static/'
            if 'static/' in qr_path:
                static_index = qr_path.find('static/')
                if static_index != -1:
                    qr_code_url = f"/{qr_path[static_index:]}"
            # Если путь абсолютный, но не содержит 'static/', проверяем существование
            elif os.path.exists(qr_path):
                # Пытаемся найти относительный путь
                cwd = os.getcwd()
                if qr_path.startswith(cwd):
                    rel_path = os.path.relpath(qr_path, cwd)
                    if rel_path.startswith('static/'):
                        qr_code_url = f"/{rel_path}"
        else:
            # Для относительного пути
            if qr_path.startswith('static/'):
                qr_code_url = f"/{qr_path}"
            elif '/' not in qr_path and '\\' not in qr_path:
                # Если это только имя файла (без директории), добавляем static/uploads/
                qr_code_url = f"/static/uploads/{qr_path}"
            else:
                qr_code_url = f"/static/{qr_path}"
    
    return {
        "phone": sbp_info.get('phone'),
        "account": sbp_info.get('account'),
        "qr_code_url": qr_code_url
    }

