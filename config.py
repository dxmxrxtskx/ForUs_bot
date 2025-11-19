"""
Модуль конфигурации бота.

Загружает:
- Токен бота из переменной окружения BOT_TOKEN (.env файл)
- Список авторизованных пользователей из config.json

API:
- load_config() - загружает и валидирует конфигурацию
- is_authorized_user(user_id) - проверяет, авторизован ли пользователь
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional


# Глобальные переменные для хранения конфигурации
BOT_TOKEN: Optional[str] = None
AUTHORIZED_USERS: Dict[int, str] = {}  # {user_id: name}


def load_config() -> None:
    """
    Загружает конфигурацию из .env и config.json.
    
    Процесс:
    1. Загружает BOT_TOKEN из переменной окружения BOT_TOKEN
    2. Загружает пользователей из config.json
    3. Валидирует, что минимум 2 пользователя
    
    Вызывает исключение, если:
    - BOT_TOKEN не найден
    - config.json не найден или некорректен
    - Меньше 2 пользователей
    """
    global BOT_TOKEN, AUTHORIZED_USERS
    
    # 1. Загрузка токена из переменной окружения
    # python-telegram-bot использует переменные окружения для токена
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError(
            "BOT_TOKEN не найден в переменных окружения. "
            "Создайте файл .env с переменной BOT_TOKEN=your_token_here"
        )
    
    # 2. Загрузка пользователей из config.json
    config_path = Path('config.json')
    if not config_path.exists():
        raise FileNotFoundError(
            f"Файл config.json не найден. "
            f"Создайте файл config.json с форматом:\n"
            f'{{"users": [{{"id": 123456789, "name": "User1"}}, {{"id": 987654321, "name": "User2"}}]}}'
        )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    # 3. Валидация структуры config.json
    if 'users' not in config_data:
        raise ValueError("config.json должен содержать ключ 'users'")
    
    users = config_data['users']
    if not isinstance(users, list):
        raise ValueError("'users' в config.json должен быть списком")
    
    if len(users) < 2:
        raise ValueError("В config.json должно быть минимум 2 пользователя")
    
    # 4. Заполнение словаря авторизованных пользователей
    AUTHORIZED_USERS = {}
    for user in users:
        if 'id' not in user or 'name' not in user:
            raise ValueError("Каждый пользователь должен иметь 'id' и 'name'")
        
        user_id = int(user['id'])
        user_name = str(user['name'])
        AUTHORIZED_USERS[user_id] = user_name
    
    print(f"✅ Конфигурация загружена: {len(AUTHORIZED_USERS)} пользователей")


def is_authorized_user(user_id: int) -> bool:
    """
    Проверяет, авторизован ли пользователь.
    
    Args:
        user_id: Telegram ID пользователя
        
    Returns:
        True если пользователь авторизован, False иначе
        
    API:
        - user_id берется из update.effective_user.id в обработчиках
        - Используется для проверки доступа во всех обработчиках
    """
    return user_id in AUTHORIZED_USERS


def get_user_name(user_id: int) -> Optional[str]:
    """
    Получает имя пользователя по его ID.
    
    Args:
        user_id: Telegram ID пользователя
        
    Returns:
        Имя пользователя или None если не найден
        
    Используется:
        - В топах для отображения имен пользователей
    """
    return AUTHORIZED_USERS.get(user_id)

