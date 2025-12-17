from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu():
    """Главное меню бота"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Мой профиль")],
            [KeyboardButton(text="🔑 Получить ключ"), KeyboardButton(text="💰 Пополнить баланс")],
            [KeyboardButton(text="📄 Инструкция")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_admin_menu():
    """Меню администратора"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Все пользователи")],
            [KeyboardButton(text="👻 Спящие профили"), KeyboardButton(text="⚠️ Должники")],
            [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_back_button():
    """Кнопка назад"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Назад")]],
        resize_keyboard=True
    )


def get_instruction_button():
    """Кнопка с инструкцией"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📖 Открыть инструкцию", url="https://github.com/amnezia-vpn/amnezia-client")]
        ]
    )
    return keyboard

