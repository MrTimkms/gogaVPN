from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Transaction, SystemSettings
from app.schemas import (
    UserResponse, BalanceAdjustment, KeyUpdate, UserMapping,
    CSVImportResponse, SettingsUpdate, SBPInfoUpdate
)
from app.services.csv_import import import_csv
from app.services.billing import get_subscription_price, set_subscription_price
from app.config import settings
from typing import List
import aiofiles

router = APIRouter(prefix="/api/admin", tags=["admin"])


def verify_admin(telegram_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    admin_ids = settings.admin_ids_list
    return telegram_id in admin_ids


@router.post("/import-csv", response_model=CSVImportResponse)
async def import_csv_file(
    file: UploadFile = File(...),
    telegram_id: int = Form(...),  # ID админа для проверки
    db: Session = Depends(get_db)
):
    """Импортирует пользователей из CSV файла"""
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV")
    
    content = await file.read()
    csv_content = content.decode('utf-8-sig')  # Обрабатываем BOM
    
    imported, errors, ghost_users = import_csv(db, csv_content)
    
    return CSVImportResponse(
        imported=imported,
        errors=errors,
        ghost_users=ghost_users
    )


@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    telegram_id: int,
    db: Session = Depends(get_db)
):
    """Получает список всех пользователей"""
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    users = db.query(User).all()
    return users


@router.get("/ghost-users", response_model=List[UserResponse])
def get_ghost_users(
    telegram_id: int,
    db: Session = Depends(get_db)
):
    """Получает список спящих профилей (без telegram_id)"""
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    users = db.query(User).filter(User.is_ghost == True).all()
    return users


@router.post("/map-user")
def map_user(
    mapping: UserMapping,
    telegram_id: int,  # ID админа
    db: Session = Depends(get_db)
):
    """Связывает спящий профиль с реальным пользователем"""
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    ghost_user = db.query(User).filter(User.id == mapping.ghost_user_id).first()
    if not ghost_user:
        raise HTTPException(status_code=404, detail="Ghost user not found")
    
    # Проверяем, не занят ли telegram_id
    existing = db.query(User).filter(
        User.telegram_id == mapping.telegram_id,
        User.id != ghost_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Telegram ID already in use")
    
    ghost_user.telegram_id = mapping.telegram_id
    ghost_user.is_ghost = False
    db.commit()
    
    return {"success": True}


@router.post("/adjust-balance")
def adjust_balance(
    adjustment: BalanceAdjustment,
    telegram_id: int,  # ID админа
    db: Session = Depends(get_db)
):
    """Корректирует баланс пользователя"""
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    user = db.query(User).filter(User.id == adjustment.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.balance += adjustment.amount
    
    # Создаем транзакцию
    transaction = Transaction(
        user_id=user.id,
        amount=adjustment.amount,
        transaction_type="adjustment",
        description=adjustment.description
    )
    db.add(transaction)
    db.commit()
    
    return {"success": True, "new_balance": user.balance}


@router.post("/update-key")
def update_key(
    key_update: KeyUpdate,
    telegram_id: int,  # ID админа
    db: Session = Depends(get_db)
):
    """Обновляет VPN ключ пользователя"""
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    user = db.query(User).filter(User.id == key_update.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.key_data = key_update.key_data
    if key_update.server_name:
        user.server_name = key_update.server_name
    
    db.commit()
    
    # Создаем уведомление
    from app.services.notifications import create_notification
    create_notification(
        db,
        user.id,
        "Вам выдан новый ключ доступа. Нажмите 'Получить ключ'.",
        "key_update"
    )
    
    return {"success": True}


@router.get("/debtors", response_model=List[UserResponse])
def get_debtors(
    telegram_id: int,
    db: Session = Depends(get_db)
):
    """Получает список должников"""
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    from app.services.billing import get_debtors
    debtors = get_debtors(db)
    return debtors


@router.get("/settings")
def get_settings(
    telegram_id: int,
    db: Session = Depends(get_db)
):
    """Получает настройки системы"""
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    price = get_subscription_price(db)
    return {"subscription_price": price}


@router.post("/settings")
def update_settings(
    settings_update: SettingsUpdate,
    telegram_id: int,
    db: Session = Depends(get_db)
):
    """Обновляет настройки системы"""
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    set_subscription_price(db, settings_update.subscription_price)
    return {"success": True}


@router.get("/sbp-info")
def get_sbp_info(
    telegram_id: int,
    db: Session = Depends(get_db)
):
    """Получает информацию о СБП"""
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    from app.services.billing import get_sbp_info
    return get_sbp_info(db)


@router.post("/sbp-info")
async def update_sbp_info(
    sbp_info: SBPInfoUpdate,
    telegram_id: int,
    db: Session = Depends(get_db)
):
    """Обновляет информацию о СБП"""
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    from app.services.billing import set_sbp_info
    
    # Обработка загрузки QR-кода
    qr_code_path = sbp_info.qr_code_path
    if qr_code_path:
        import os
        # Если это только имя файла (без директории), добавляем static/uploads/
        if '/' not in qr_code_path and '\\' not in qr_code_path and not os.path.isabs(qr_code_path):
            qr_code_path = f"static/uploads/{qr_code_path}"
            os.makedirs("static/uploads", exist_ok=True)
        elif not qr_code_path.startswith('static/') and not os.path.isabs(qr_code_path):
            # Если путь относительный, но не начинается с static/, добавляем
            qr_code_path = f"static/uploads/{qr_code_path}"
            os.makedirs("static/uploads", exist_ok=True)
    
    set_sbp_info(
        db,
        phone=sbp_info.phone,
        account=sbp_info.account,
        qr_code_path=qr_code_path
    )
    
    return {"success": True}


@router.post("/upload-qr")
async def upload_qr_code(
    file: UploadFile = File(...),
    telegram_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Загружает QR-код для СБП"""
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    import os
    import uuid
    
    # Создаем директорию если нет
    upload_dir = "static/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Генерируем уникальное имя файла
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'png'
    filename = f"sbp_qr_{uuid.uuid4().hex[:8]}.{file_ext}"
    file_path = os.path.join(upload_dir, filename)
    
    # Сохраняем файл
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Сохраняем путь в настройках
    from app.services.billing import set_sbp_info
    set_sbp_info(db, qr_code_path=file_path)
    
    return {"success": True, "file_path": file_path}

