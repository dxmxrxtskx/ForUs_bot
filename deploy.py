"""
Скрипт автоматического развертывания бота.
Создает необходимые файлы и директории.
"""

import os
import json
from pathlib import Path


def create_env_file():
    """Создает файл .env если его нет."""
    env_path = Path('.env')
    if not env_path.exists():
        print("Создаю файл .env...")
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write("BOT_TOKEN=your_bot_token_here\n")
        print("✅ Файл .env создан. Заполните BOT_TOKEN!")
    else:
        print("✅ Файл .env уже существует")


def create_config_json():
    """Создает файл config.json если его нет."""
    config_path = Path('config.json')
    if not config_path.exists():
        print("Создаю файл config.json...")
        config = {
            "users": [
                {
                    "id": 123456789,
                    "name": "User1"
                },
                {
                    "id": 987654321,
                    "name": "User2"
                }
            ]
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("✅ Файл config.json создан. Заполните ID пользователей!")
    else:
        print("✅ Файл config.json уже существует")


def create_data_dir():
    """Создает директорию data/ если её нет."""
    data_path = Path('data')
    if not data_path.exists():
        print("Создаю директорию data/...")
        data_path.mkdir()
        print("✅ Директория data/ создана")
    else:
        print("✅ Директория data/ уже существует")


def main():
    """Главная функция развертывания."""
    print("🚀 Начало развертывания бота...\n")
    
    create_env_file()
    create_config_json()
    create_data_dir()
    
    print("\n✅ Развертывание завершено!")
    print("\n📝 Следующие шаги:")
    print("1. Заполните BOT_TOKEN в файле .env")
    print("2. Заполните ID пользователей в файле config.json")
    print("3. Запустите бота: python bot.py")
    print("   Или через Docker: docker-compose up -d")


if __name__ == '__main__':
    main()

