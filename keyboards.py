"""
Модуль для построения клавиатур Telegram бота.

Два типа клавиатур:
1. ReplyKeyboardMarkup - постоянная клавиатура внизу экрана
2. InlineKeyboardMarkup - кнопки под сообщением (для callback queries)
"""

from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional, Dict, Any


# Список всех разделов бота
SECTIONS = [
    "Фильмы",
    "Активности",
    "Поездки",
    "Тренды TikTok",
    "Фотографии",
    "Игры",
    "Sexual"
]


def main_menu_reply_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает главное меню - Reply Keyboard (постоянная клавиатура).
    
    Returns:
        ReplyKeyboardMarkup с 7 кнопками разделов
    """
    # Размещаем кнопки по 2 в ряд для удобства
    keyboard = [
        [SECTIONS[0], SECTIONS[1]],  # Фильмы, Активности
        [SECTIONS[2], SECTIONS[3]],  # Поездки, Тренды TikTok
        [SECTIONS[4], SECTIONS[5]],  # Фотографии, Игры
        [SECTIONS[6]]                # Sexual
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def main_menu_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Создает главное меню - Inline Keyboard (для callback queries).
    
    Returns:
        InlineKeyboardMarkup с 7 кнопками разделов
    """
    buttons = []
    # Размещаем по 2 кнопки в ряд
    for i in range(0, len(SECTIONS), 2):
        row = []
        row.append(InlineKeyboardButton(SECTIONS[i], callback_data=f"section_{SECTIONS[i]}"))
        if i + 1 < len(SECTIONS):
            row.append(InlineKeyboardButton(SECTIONS[i + 1], callback_data=f"section_{SECTIONS[i + 1]}"))
        buttons.append(row)
    
    return InlineKeyboardMarkup(buttons)


def back_button(callback_data: str) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с одной кнопкой "Назад".
    
    Args:
        callback_data: callback_data для кнопки "Назад"
        
    Returns:
        InlineKeyboardMarkup с кнопкой "Назад"
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data=callback_data)]
    ])


def main_menu_button() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопкой "Главное меню".
    
    Returns:
        InlineKeyboardMarkup с кнопкой "Главное меню"
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ])


def list_keyboard(
    items: List[Any],
    page: int,
    items_per_page: int,
    callback_prefix: str,
    back_callback: str,
    custom_back_text: Optional[str] = None
) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для списка с пагинацией.
    
    Args:
        items: Список элементов для отображения
        page: Номер текущей страницы (начиная с 0)
        items_per_page: Количество элементов на странице (обычно 10)
        callback_prefix: Префикс для callback_data (например, "movie_")
        back_callback: callback_data для кнопки "Назад"
        custom_back_text: Текст для кнопки "Назад" (по умолчанию "◀️ Назад")
        
    Returns:
        InlineKeyboardMarkup с элементами списка и навигацией
    """
    buttons = []
    
    # Вычисляем индексы для текущей страницы
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_items = items[start_idx:end_idx]
    
    # Создаем кнопки для элементов текущей страницы
    for item in page_items:
        # Предполагаем, что у элемента есть id и title
        item_id = item['id'] if isinstance(item, dict) else item.id
        item_title = item['title'] if isinstance(item, dict) else item.title
        
        # Ограничиваем длину текста кнопки (Telegram лимит ~64 символа)
        button_text = item_title[:60] + "..." if len(item_title) > 60 else item_title
        
        buttons.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"{callback_prefix}{item_id}"
            )
        ])
    
    # Навигационные кнопки
    nav_buttons = []
    
    # Кнопка "Назад" (влево)
    back_text = custom_back_text if custom_back_text else "◀️ Назад"
    nav_buttons.append(InlineKeyboardButton(back_text, callback_data=back_callback))
    
    # Кнопки пагинации (если нужно)
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"{callback_prefix}page_{page - 1}"))
    
    if end_idx < len(items):
        nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"{callback_prefix}page_{page + 1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    return InlineKeyboardMarkup(buttons)


def rating_keyboard(callback_prefix: str, item_id: int, user_num: int) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для оценки (1-10).
    
    Args:
        callback_prefix: Префикс для callback_data (например, "rate_movie_")
        item_id: ID элемента для оценки
        user_num: Номер пользователя (1 или 2)
        
    Returns:
        InlineKeyboardMarkup с кнопками от 1 до 10 и "Отмена"
    """
    buttons = []
    
    # Кнопки оценок по 5 в ряд
    for i in range(0, 10, 5):
        row = []
        for j in range(i + 1, min(i + 6, 11)):
            row.append(InlineKeyboardButton(
                str(j),
                callback_data=f"{callback_prefix}{item_id}_user{user_num}_{j}"
            ))
        buttons.append(row)
    
    # Кнопка "Отмена"
    buttons.append([
        InlineKeyboardButton("❌ Отмена", callback_data=f"{callback_prefix}cancel_{item_id}")
    ])
    
    return InlineKeyboardMarkup(buttons)


def yes_no_keyboard(yes_callback: str, no_callback: str) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопками "Да" и "Нет".
    
    Args:
        yes_callback: callback_data для "Да"
        no_callback: callback_data для "Нет"
        
    Returns:
        InlineKeyboardMarkup с кнопками "Да" и "Нет"
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Да", callback_data=yes_callback),
            InlineKeyboardButton("❌ Нет", callback_data=no_callback)
        ]
    ])


def cancel_button(callback_data: str = "cancel") -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопкой "Отмена".
    
    Args:
        callback_data: callback_data для кнопки "Отмена"
        
    Returns:
        InlineKeyboardMarkup с кнопкой "Отмена"
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Отмена", callback_data=callback_data)]
    ])

