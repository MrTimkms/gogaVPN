from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Transaction, SystemSettings, Server
from app.schemas import (
    UserResponse, BalanceAdjustment, KeyUpdate, UserMapping,
    CSVImportResponse, SettingsUpdate, SBPInfoUpdate, UserUpdate,
    SendNotificationRequest, ServerCreate, ServerUpdate, ServerResponse
)
from app.services.csv_import import import_csv
from app.services.billing import get_subscription_price, set_subscription_price
from app.config import settings
from typing import List
import aiofiles

router = APIRouter(prefix="/api/admin", tags=["admin"])


def verify_admin(telegram_id: int) -> bool:
    admin_ids = settings.admin_ids_list
    return telegram_id in admin_ids


@router.post("/import-csv", response_model=CSVImportResponse)
async def import_csv_file(
    file: UploadFile = File(...),
    telegram_id: int = Form(...),
    db: Session = Depends(get_db)
):
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
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    users = db.query(User).all()
    return users


@router.get("/ghost-users", response_model=List[UserResponse])
def get_ghost_users(
    telegram_id: int,
    db: Session = Depends(get_db)
):
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    users = db.query(User).filter(User.is_ghost == True).all()
    return users


@router.post("/map-user")
def map_user(
    mapping: UserMapping,
    telegram_id: int,
    db: Session = Depends(get_db)
):
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    ghost_user = db.query(User).filter(User.id == mapping.ghost_user_id).first()
    if not ghost_user:
        raise HTTPException(status_code=404, detail="Ghost user not found")
    
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
    telegram_id: int,
    db: Session = Depends(get_db)
):
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    user = db.query(User).filter(User.id == adjustment.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.balance += adjustment.amount
    
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
    telegram_id: int,
    db: Session = Depends(get_db)
):
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    user = db.query(User).filter(User.id == key_update.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.key_data = key_update.key_data
    if key_update.server_name:
        user.server_name = key_update.server_name
    
    db.commit()
    
    from app.services.notifications import create_notification
    create_notification(
        db,
        user.id,
        "Вам выдан новый ключ доступа. Нажмите 'Получить ключ'.",
        "key_update"
    )
    
    return {"success": True}


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    user_update: UserUpdate,
    telegram_id: int,
    db: Session = Depends(get_db)
):
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Обновляем поля, если они переданы
    if user_update.name is not None:
        user.name = user_update.name
    if user_update.balance is not None:
        user.balance = user_update.balance
    if user_update.next_billing_date is not None:
        user.next_billing_date = user_update.next_billing_date
    if user_update.start_date is not None:
        user.start_date = user_update.start_date
    if user_update.status is not None:
        user.status = user_update.status
    if user_update.enable_billing_notifications is not None:
        user.enable_billing_notifications = user_update.enable_billing_notifications
    if user_update.notify_before_billing_days is not None:
        # Проверяем, что значение в разумных пределах (0-30 дней)
        if not (0 <= user_update.notify_before_billing_days <= 30):
            raise HTTPException(status_code=400, detail="notify_before_billing_days must be between 0 and 30")
        user.notify_before_billing_days = user_update.notify_before_billing_days
    if user_update.enable_negative_balance_notifications is not None:
        user.enable_negative_balance_notifications = user_update.enable_negative_balance_notifications
    if user_update.certificates_count is not None:
        if user_update.certificates_count < 1:
            raise HTTPException(status_code=400, detail="certificates_count must be at least 1")
        user.certificates_count = user_update.certificates_count
    if user_update.server_name is not None:
        user.server_name = user_update.server_name
    
    db.commit()
    db.refresh(user)
    
    return {"success": True, "user": UserResponse.model_validate(user)}


@router.get("/debtors", response_model=List[UserResponse])
def get_debtors(
    telegram_id: int,
    db: Session = Depends(get_db)
):
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
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    set_subscription_price(db, settings_update.subscription_price)
    return {"success": True}


@router.get("/sbp-info")
def get_sbp_info(
    telegram_id: int,
    db: Session = Depends(get_db)
):
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
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    from app.services.billing import set_sbp_info
    set_sbp_info(db, qr_code_path=file_path)
    
    return {"success": True, "file_path": file_path}


@router.post("/send-notification")
def send_notification_to_user(
    request: SendNotificationRequest,
    telegram_id: int,
    db: Session = Depends(get_db)
):
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.telegram_id:
        raise HTTPException(status_code=400, detail="User has no Telegram ID")
    
    from app.services.notifications import create_notification
    create_notification(
        db,
        user.id,
        request.message,
        "admin_message"
    )
    
    return {"success": True, "message": "Уведомление создано и будет отправлено в ближайшее время"}


@router.post("/servers", response_model=ServerResponse)
def create_server(
    server: ServerCreate,
    telegram_id: int,
    db: Session = Depends(get_db)
):
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    existing = db.query(Server).filter(Server.name == server.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Server with this name already exists")
    
    new_server = Server(name=server.name, ip_address=server.ip_address)
    db.add(new_server)
    db.commit()
    db.refresh(new_server)
    
    return new_server


@router.get("/servers", response_model=List[ServerResponse])
def get_servers(
    telegram_id: int,
    db: Session = Depends(get_db)
):
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    servers = db.query(Server).all()
    return servers


@router.put("/servers/{server_id}", response_model=ServerResponse)
def update_server(
    server_id: int,
    server_update: ServerUpdate,
    telegram_id: int,
    db: Session = Depends(get_db)
):
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    if server_update.name is not None:
        existing = db.query(Server).filter(Server.name == server_update.name, Server.id != server_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Server with this name already exists")
        server.name = server_update.name
    
    if server_update.ip_address is not None:
        server.ip_address = server_update.ip_address
    
    db.commit()
    db.refresh(server)
    
    return server


@router.delete("/servers/{server_id}")
def delete_server(
    server_id: int,
    telegram_id: int,
    db: Session = Depends(get_db)
):
    if not verify_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    users_with_server = db.query(User).filter(User.server_name == server.name).count()
    if users_with_server > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete server: {users_with_server} user(s) are using it"
        )
    
    db.delete(server)
    db.commit()
    
    return {"success": True}

