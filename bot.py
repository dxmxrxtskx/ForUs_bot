"""
Главный файл бота - инициализация и регистрация всех обработчиков.
"""

import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

import config
import database
from keyboards import main_menu_reply_keyboard, main_menu_inline_keyboard

# Загружаем переменные окружения из .env
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def check_authorization(func):
    """Декоратор для проверки авторизации пользователя."""
    async def wrapper(update: Update, context):
        user_id = update.effective_user.id
        if not config.is_authorized_user(user_id):
            await update.message.reply_text("❌ У вас нет доступа к этому боту.")
            return
        return await func(update, context)
    return wrapper


async def start(update: Update, context) -> None:
    """Обработчик команды /start."""
    user_id = update.effective_user.id
    
    if not config.is_authorized_user(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    welcome_text = f"👋 Привет, {update.effective_user.first_name}!\n\nВыберите раздел:"
    await update.message.reply_text(
        welcome_text,
        reply_markup=main_menu_reply_keyboard()
    )


async def main_menu_handler(update: Update, context) -> None:
    """Обработчик главного меню (reply keyboard)."""
    user_id = update.effective_user.id
    
    if not config.is_authorized_user(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    text = update.message.text
    
    # Импортируем обработчики разделов
    if text == "Фильмы":
        from handlers.movies import movies_menu
        await movies_menu(update, context)
    elif text == "Активности":
        from handlers.activities import activities_menu
        await activities_menu(update, context)
    elif text == "Поездки":
        from handlers.trips import trips_menu
        await trips_menu(update, context)
    elif text == "Тренды TikTok":
        from handlers.tiktok import tiktok_menu
        await tiktok_menu(update, context)
    elif text == "Фотографии":
        from handlers.photos import photos_menu
        await photos_menu(update, context)
    elif text == "Игры":
        from handlers.games import games_menu
        await games_menu(update, context)
    elif text == "Sexual":
        from handlers.sexual import sexual_menu
        await sexual_menu(update, context)


async def main_menu_callback(update: Update, context) -> None:
    """Обработчик callback для главного меню (inline keyboard)."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not config.is_authorized_user(user_id):
        await query.edit_message_text("❌ У вас нет доступа к этому боту.")
        return
    
    if query.data == "main_menu":
        text = "🏠 Главное меню\n\nВыберите раздел:"
        try:
            await query.edit_message_text(
                text,
                reply_markup=main_menu_inline_keyboard()
            )
        except Exception as e:
            # Если сообщение не может быть отредактировано, отправляем новое
            await query.message.reply_text(
                text,
                reply_markup=main_menu_inline_keyboard()
            )
    
    # Обработка выбора раздела через callback
    elif query.data.startswith("section_"):
        section = query.data.replace("section_", "")
        
        if section == "Фильмы":
            from handlers.movies import movies_menu
            await movies_menu(update, context)
        elif section == "Активности":
            from handlers.activities import activities_menu
            await activities_menu(update, context)
        elif section == "Поездки":
            from handlers.trips import trips_menu
            await trips_menu(update, context)
        elif section == "Тренды TikTok":
            from handlers.tiktok import tiktok_menu
            await tiktok_menu(update, context)
        elif section == "Фотографии":
            from handlers.photos import photos_menu
            await photos_menu(update, context)
        elif section == "Игры":
            from handlers.games import games_menu
            await games_menu(update, context)
        elif section == "Sexual":
            from handlers.sexual import sexual_menu
            await sexual_menu(update, context)


def main() -> None:
    """Главная функция - запуск бота."""
    # Загружаем конфигурацию
    try:
        config.load_config()
    except Exception as e:
        logger.error(f"Ошибка загрузки конфигурации: {e}")
        return
    
    # Инициализируем базу данных
    try:
        database.init_database()
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        return
    
    # Создаем приложение бота
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN не найден в переменных окружения")
        return
    
    application = Application.builder().token(bot_token).build()
    
    # Регистрируем обработчики главного меню (высокий приоритет)
    application.add_handler(CommandHandler("start", start), group=0)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler), group=0)
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^(main_menu|section_.+)$"), group=0)
    
    # Импортируем и регистрируем обработчики разделов
    from handlers import movies, activities, trips, tiktok, photos, games, sexual
    
    # Регистрируем обработчики разделов (низкий приоритет)
    movies.register_handlers(application)
    activities.register_handlers(application)
    trips.register_handlers(application)
    tiktok.register_handlers(application)
    photos.register_handlers(application)
    games.register_handlers(application)
    sexual.register_handlers(application)
    
    # Запускаем бота
    logger.info("Бот запущен")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

