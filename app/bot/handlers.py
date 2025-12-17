from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, Transaction
from app.services.billing import get_subscription_price
from app.services.notifications import create_notification
from app.config import settings
from app.bot.keyboards import get_main_menu, get_admin_menu, get_instruction_button
from datetime import date
import logging

logger = logging.getLogger(__name__)

router = Router()


class PaymentStates(StatesGroup):
    waiting_for_screenshot = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
        
        if not user:
            # Создаем нового пользователя
            user = User(
                telegram_id=message.from_user.id,
                name=message.from_user.first_name or "Пользователь",
                balance=0.0,
                start_date=date.today(),
                next_billing_date=date.today(),
                status="active",
                is_ghost=False
            )
            db.add(user)
            db.commit()
            
            await message.answer(
                "👋 Добро пожаловать! Вы зарегистрированы в системе.\n\n"
                "Используйте меню для навигации.",
                reply_markup=get_main_menu()
            )
        else:
            if user.is_ghost:
                await message.answer(
                    "⚠️ Ваш профиль еще не активирован администратором. "
                    "Ожидайте подтверждения.",
                    reply_markup=get_main_menu()
                )
            else:
                await message.answer(
                    "👋 С возвращением! Используйте меню для навигации.",
                    reply_markup=get_main_menu()
                )
    finally:
        db.close()


@router.message(F.text == "👤 Мой профиль")
async def show_profile(message: Message):
    """Показывает профиль пользователя"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
        if not user:
            await message.answer("❌ Пользователь не найден. Используйте /start")
            return
        
        price = get_subscription_price(db)
        status_emoji = "✅" if user.status == "active" else "❌"
        status_text = "Активен" if user.status == "active" else "Заблокирован" if user.status == "blocked" else "Задолженность"
        
        text = (
            f"👤 <b>Мой профиль</b>\n\n"
            f"Имя: {user.name}\n"
            f"Баланс: {user.balance:.2f} ₽\n"
            f"Тариф: {price:.2f} ₽/мес\n"
            f"Следующее списание: {user.next_billing_date.strftime('%d.%m.%Y')}\n"
            f"Статус: {status_emoji} {status_text}"
        )
        
        await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu())
    finally:
        db.close()


@router.message(F.text == "🔑 Получить ключ")
async def get_key(message: Message):
    """Выдает VPN ключ пользователю"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
        if not user:
            await message.answer("❌ Пользователь не найден")
            return
        
        if not user.key_data:
            await message.answer(
                "❌ Ключ еще не загружен администратором. "
                "Ожидайте получения ключа.",
                reply_markup=get_main_menu()
            )
            return
        
        # Отправляем ключ как файл
        from aiogram.types import BufferedInputFile
        key_bytes = user.key_data.encode('utf-8')
        key_file = BufferedInputFile(key_bytes, filename="vpn_config.vpn")
        
        await message.answer_document(
            document=key_file,
            caption="🔑 Ваш VPN ключ доступа"
        )
        
        # Также отправляем текстовый вариант
        await message.answer(
            f"📋 Текстовый ключ:\n<code>{user.key_data}</code>",
            parse_mode="HTML"
        )
    finally:
        db.close()


@router.message(F.text == "💰 Пополнить баланс")
async def show_payment_info(message: Message, state: FSMContext):
    """Показывает реквизиты для пополнения через СБП"""
    db = SessionLocal()
    try:
        from app.services.billing import get_sbp_info
        
        sbp_info = get_sbp_info(db)
        
        payment_info = (
            "💰 <b>Пополнение баланса</b>\n\n"
            "💳 <b>Оплата через СБП:</b>\n"
        )
        
        if sbp_info.get('phone'):
            payment_info += f"📱 Телефон: <code>{sbp_info['phone']}</code>\n"
        
        if sbp_info.get('account'):
            payment_info += f"🏦 Счет: <code>{sbp_info['account']}</code>\n"
        
        payment_info += (
            "\n📝 <b>Как оплатить:</b>\n"
            "1. Откройте приложение вашего банка\n"
            "2. Выберите 'Оплата по QR-коду' или 'Перевод по номеру телефона'\n"
            "3. Отсканируйте QR-код или введите номер телефона\n"
            "4. Укажите сумму пополнения\n"
            "5. После оплаты отправьте скриншот чека\n\n"
            "💡 <i>Или используйте автоплатеж для автоматического пополнения</i>"
        )
        
        await message.answer(payment_info, parse_mode="HTML")
        
        # Отправляем QR-код если есть
        if sbp_info.get('qr_code_path'):
            try:
                from aiogram.types import FSInputFile
                qr_file = FSInputFile(sbp_info['qr_code_path'])
                await message.answer_photo(
                    photo=qr_file,
                    caption="📱 QR-код для оплаты через СБП"
                )
            except Exception as e:
                logger.error(f"Ошибка отправки QR-кода: {e}")
        
        await state.set_state(PaymentStates.waiting_for_screenshot)
    finally:
        db.close()


@router.message(PaymentStates.waiting_for_screenshot, F.photo)
async def process_payment_screenshot(message: Message, state: FSMContext):
    """Обрабатывает скриншот чека"""
    bot = message.bot
    await message.answer(
        "✅ Скриншот получен. Администратор проверит оплату и пополнит ваш баланс.\n"
        "Обычно это занимает несколько часов.",
        reply_markup=get_main_menu()
    )
    await state.clear()
    
    # Уведомляем админов
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
        if user:
            # Отправляем уведомление админам
            from app.config import settings
            admin_message = (
                f"📸 Новый скриншот оплаты от пользователя:\n"
                f"Имя: {user.name}\n"
                f"Telegram ID: {user.telegram_id}\n"
                f"Текущий баланс: {user.balance:.2f} ₽"
            )
            
            # Пересылаем фото админам
            for admin_id in settings.admin_ids_list:
                try:
                    await bot.forward_message(
                        chat_id=admin_id,
                        from_chat_id=message.chat.id,
                        message_id=message.message_id
                    )
                    await bot.send_message(admin_id, admin_message)
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления админу {admin_id}: {e}")
    finally:
        db.close()


@router.message(F.text == "📄 Инструкция")
async def show_instruction(message: Message):
    """Показывает инструкцию по установке"""
    instruction = (
        "📄 <b>Инструкция по установке Amnezia VPN</b>\n\n"
        "1. Скачайте приложение Amnezia VPN:\n"
        "   • Android: Google Play\n"
        "   • iOS: App Store\n"
        "   • Windows/Mac/Linux: https://github.com/amnezia-vpn/amnezia-client\n\n"
        "2. Откройте приложение\n"
        "3. Нажмите 'Добавить конфигурацию'\n"
        "4. Выберите 'Импорт из файла' или вставьте ключ вручную\n"
        "5. Подключитесь к серверу\n\n"
        "Если возникли проблемы, обратитесь к администратору."
    )
    
    await message.answer(
        instruction,
        parse_mode="HTML",
        reply_markup=get_instruction_button()
    )


# Админские команды
def is_admin(telegram_id: int) -> bool:
    """Проверяет, является ли пользователь админом"""
    return telegram_id in settings.admin_ids_list


@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Открывает админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return
    
    await message.answer(
        "⚙️ <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_admin_menu()
    )


@router.message(F.text == "⚠️ Должники")
async def show_debtors(message: Message):
    """Показывает список должников"""
    if not is_admin(message.from_user.id):
        return
    
    db = SessionLocal()
    try:
        from app.services.billing import get_debtors
        debtors = get_debtors(db)
        
        if not debtors:
            await message.answer("✅ Должников нет")
            return
        
        text = "⚠️ <b>Список должников:</b>\n\n"
        for user in debtors:
            text += f"• {user.name} (@{user.telegram_id})\n"
            text += f"  Баланс: {user.balance:.2f} ₽\n\n"
        
        await message.answer(text, parse_mode="HTML")
    finally:
        db.close()


@router.message(F.text == "💳 СБП настройки")
async def sbp_settings(message: Message):
    """Настройки СБП"""
    if not is_admin(message.from_user.id):
        return
    
    db = SessionLocal()
    try:
        from app.services.billing import get_sbp_info
        sbp_info = get_sbp_info(db)
        
        text = "💳 <b>Настройки СБП</b>\n\n"
        
        if sbp_info.get('phone'):
            text += f"📱 Телефон: <code>{sbp_info['phone']}</code>\n"
        else:
            text += "📱 Телефон: <i>не настроен</i>\n"
        
        if sbp_info.get('account'):
            text += f"🏦 Счет: <code>{sbp_info['account']}</code>\n"
        else:
            text += "🏦 Счет: <i>не настроен</i>\n"
        
        if sbp_info.get('qr_code_path'):
            text += "✅ QR-код загружен\n"
        else:
            text += "❌ QR-код не загружен\n"
        
        text += "\n💡 Для изменения настроек используйте веб-админ-панель:\n"
        text += "http://ваш_сервер:8080/admin"
        
        await message.answer(text, parse_mode="HTML")
        
        # Отправляем QR-код если есть
        if sbp_info.get('qr_code_path'):
            try:
                from aiogram.types import FSInputFile
                import os
                qr_path = sbp_info['qr_code_path']
                # Если путь относительный, делаем абсолютным
                if not os.path.isabs(qr_path):
                    qr_path = os.path.join(os.getcwd(), qr_path)
                if os.path.exists(qr_path):
                    qr_file = FSInputFile(qr_path)
                    await message.answer_photo(
                        photo=qr_file,
                        caption="📱 QR-код для оплаты через СБП"
                    )
            except Exception as e:
                logger.error(f"Ошибка отправки QR-кода: {e}")
    finally:
        db.close()


@router.message(F.text == "🔙 Главное меню")
async def back_to_main(message: Message):
    """Возврат в главное меню"""
    await message.answer("Главное меню", reply_markup=get_main_menu())

