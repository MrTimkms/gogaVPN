import csv
import io
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import User
from typing import List, Dict, Tuple


def parse_date(date_str: str) -> datetime.date:
    """Парсит дату в формате ДД.ММ.ГГГГ"""
    try:
        return datetime.strptime(date_str.strip(), "%d.%m.%Y").date()
    except ValueError:
        raise ValueError(f"Неверный формат даты: {date_str}. Ожидается ДД.ММ.ГГГГ")


def import_csv(db: Session, csv_content: str) -> Tuple[int, List[Dict], int]:
    """
    Импортирует пользователей из CSV
    Returns: (imported_count, errors, ghost_users_count)
    """
    imported = 0
    errors = []
    ghost_users = 0
    
    # Читаем CSV с разделителем точка с запятой
    reader = csv.DictReader(io.StringIO(csv_content), delimiter=';')
    
    for row_num, row in enumerate(reader, start=2):  # Начинаем с 2, т.к. первая строка - заголовок
        try:
            # Парсим данные
            telegram_id = None
            if row.get('telegram_id', '').strip():
                try:
                    telegram_id = int(row['telegram_id'].strip())
                except ValueError:
                    errors.append({
                        'row': row_num,
                        'field': 'telegram_id',
                        'error': f"Неверный формат telegram_id: {row['telegram_id']}"
                    })
                    continue
            
            name = row.get('name', '').strip()
            if not name:
                errors.append({
                    'row': row_num,
                    'field': 'name',
                    'error': 'Имя не может быть пустым'
                })
                continue
            
            try:
                start_date = parse_date(row.get('start_date', ''))
            except ValueError as e:
                errors.append({
                    'row': row_num,
                    'field': 'start_date',
                    'error': str(e)
                })
                continue
            
            try:
                balance = float(row.get('balance', '0').strip().replace(',', '.'))
            except ValueError:
                balance = 0.0
            
            key_data = row.get('key_data', '').strip() or None
            
            # Проверяем, существует ли пользователь с таким telegram_id
            if telegram_id:
                existing_user = db.query(User).filter(User.telegram_id == telegram_id).first()
                if existing_user:
                    errors.append({
                        'row': row_num,
                        'field': 'telegram_id',
                        'error': f'Пользователь с telegram_id {telegram_id} уже существует'
                    })
                    continue
            
            # Создаем пользователя
            user = User(
                telegram_id=telegram_id,
                name=name,
                balance=balance,
                start_date=start_date,
                next_billing_date=start_date,  # Первое списание в день старта
                status="active",
                key_data=key_data,
                is_ghost=(telegram_id is None)
            )
            
            db.add(user)
            imported += 1
            
            if not telegram_id:
                ghost_users += 1
                
        except Exception as e:
            errors.append({
                'row': row_num,
                'field': 'general',
                'error': f'Ошибка обработки строки: {str(e)}'
            })
    
    db.commit()
    return imported, errors, ghost_users

