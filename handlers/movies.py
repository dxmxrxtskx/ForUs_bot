"""
Обработчики для раздела "Фильмы".
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, ConversationHandler, filters
import database
import config
from keyboards import list_keyboard, back_button, main_menu_button, rating_keyboard


# Состояния для ConversationHandler
MOVIE_TITLE, MOVIE_NOTE, MOVIE_CATEGORY = range(3)
EDIT_MOVIE_TITLE, EDIT_MOVIE_NOTE = range(3, 5)
RATING_USER1, RATING_USER2 = range(5, 7)


async def movies_menu(update: Update, context) -> None:
    """Меню раздела фильмы."""
    keyboard = [
        [InlineKeyboardButton("📋 Ожидающие просмотра", callback_data="movies_pending")],
        [InlineKeyboardButton("✅ Просмотренные", callback_data="movies_watched")],
        [InlineKeyboardButton("🎲 Случайный фильм", callback_data="movies_random")],
        [InlineKeyboardButton("➕ Добавить фильм", callback_data="movies_add")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text("🎬 Раздел: Фильмы\n\nВыберите действие:", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("🎬 Раздел: Фильмы\n\nВыберите действие:", reply_markup=reply_markup)


async def movies_pending_menu(update: Update, context) -> None:
    """Подменю ожидающих фильмов."""
    query = update.callback_query
    await query.answer()
    
    categories = database.get_movie_categories()
    keyboard = [
        [InlineKeyboardButton("📋 Общий список", callback_data="movies_pending_all")]
    ]
    
    for cat in categories:
        keyboard.append([InlineKeyboardButton(f"📁 {cat['title']}", callback_data=f"movies_pending_cat_{cat['id']}")])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="movies_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("📋 Ожидающие просмотра\n\nВыберите категорию:", reply_markup=reply_markup)


async def movies_pending_list(update: Update, context) -> None:
    """Список ожидающих фильмов."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == "movies_pending_all":
        movies = database.get_movies(watched=0)
        category_id = None
    else:
        category_id = int(data.split("_")[-1])
        movies = database.get_movies(watched=0, category_id=category_id)
    
    if not movies:
        text = "📋 Список пуст"
        keyboard = back_button("movies_pending")
    else:
        text = f"📋 Ожидающие просмотра ({len(movies)}):\n\n"
        for i, movie in enumerate(movies[:10], 1):
            text += f"{i}. {movie['title']}\n"
        
        if len(movies) > 10:
            text += f"\n... и еще {len(movies) - 10}"
        
        keyboard = list_keyboard(
            movies,
            page=0,
            items_per_page=10,
            callback_prefix="movie_",
            back_callback="movies_pending"
        )
    
    await query.edit_message_text(text, reply_markup=keyboard)


async def movie_detail(update: Update, context) -> None:
    """Детальный просмотр фильма."""
    query = update.callback_query
    await query.answer()
    
    movie_id = int(query.data.split("_")[1])
    movie = database.get_movie_by_id(movie_id)
    
    if not movie:
        await query.edit_message_text("❌ Фильм не найден")
        return
    
    text = f"🎬 {movie['title']}\n\n"
    if movie['note']:
        text += f"📝 {movie['note']}\n\n"
    text += f"📁 Категория: {movie['category_title']}\n"
    
    if movie['watched']:
        text += f"✅ Просмотрен\n"
        if movie['user1_rating']:
            user1_name = config.get_user_name(list(config.AUTHORIZED_USERS.keys())[0]) or "Пользователь 1"
            text += f"⭐ {user1_name}: {movie['user1_rating']}/10\n"
        if movie['user2_rating']:
            user2_name = config.get_user_name(list(config.AUTHORIZED_USERS.keys())[1]) or "Пользователь 2"
            text += f"⭐ {user2_name}: {movie['user2_rating']}/10\n"
    else:
        text += "⏳ Ожидает просмотра\n"
    
    keyboard = []
    if not movie['watched']:
        keyboard.append([InlineKeyboardButton("✅ Просмотрен", callback_data=f"movie_watched_{movie_id}")])
    keyboard.append([InlineKeyboardButton("✏️ Редактировать", callback_data=f"movie_edit_{movie_id}")])
    keyboard.append([InlineKeyboardButton("🗑 Удалить", callback_data=f"movie_delete_{movie_id}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="movies_pending")])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def movies_watched_menu(update: Update, context) -> None:
    """Меню просмотренных фильмов."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📋 Общий список", callback_data="movies_watched_all")],
        [InlineKeyboardButton("🏆 Топ-10", callback_data="movies_top")],
        [InlineKeyboardButton("◀️ Назад", callback_data="movies_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("✅ Просмотренные\n\nВыберите действие:", reply_markup=reply_markup)


async def movies_watched_list(update: Update, context) -> None:
    """Список просмотренных фильмов."""
    query = update.callback_query
    await query.answer()
    
    movies = database.get_movies(watched=1)
    
    if not movies:
        text = "📋 Список пуст"
        keyboard = back_button("movies_watched")
    else:
        text = f"✅ Просмотренные ({len(movies)}):\n\n"
        for i, movie in enumerate(movies[:10], 1):
            rating_text = ""
            if movie['user1_rating'] and movie['user2_rating']:
                avg = (movie['user1_rating'] + movie['user2_rating']) / 2
                rating_text = f" - {avg:.1f}/10"
            text += f"{i}. {movie['title']}{rating_text}\n"
        
        if len(movies) > 10:
            text += f"\n... и еще {len(movies) - 10}"
        
        keyboard = list_keyboard(
            movies,
            page=0,
            items_per_page=10,
            callback_prefix="movie_",
            back_callback="movies_watched"
        )
    
    await query.edit_message_text(text, reply_markup=keyboard)


async def movies_top_menu(update: Update, context) -> None:
    """Меню топ-10 фильмов."""
    query = update.callback_query
    await query.answer()
    
    user_ids = list(config.AUTHORIZED_USERS.keys())
    user1_name = config.get_user_name(user_ids[0]) or "Пользователь 1"
    user2_name = config.get_user_name(user_ids[1]) if len(user_ids) > 1 else "Пользователь 2"
    
    keyboard = [
        [InlineKeyboardButton("🏆 Общий топ", callback_data="movies_top_all")],
        [InlineKeyboardButton(f"⭐ {user1_name}", callback_data="movies_top_user1")],
        [InlineKeyboardButton(f"⭐ {user2_name}", callback_data="movies_top_user2")],
        [InlineKeyboardButton("◀️ Назад", callback_data="movies_watched")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("🏆 Топ-10 фильмов\n\nВыберите топ:", reply_markup=reply_markup)


async def movies_top_show(update: Update, context) -> None:
    """Показать топ-10 фильмов."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == "movies_top_all":
        movies = database.get_movies_top(limit=10, user_num=None)
        title = "🏆 Общий топ-10:"
    elif data == "movies_top_user1":
        movies = database.get_movies_top(limit=10, user_num=1)
        user1_name = config.get_user_name(list(config.AUTHORIZED_USERS.keys())[0]) or "Пользователь 1"
        title = f"⭐ Топ-10 {user1_name}:"
    else:
        movies = database.get_movies_top(limit=10, user_num=2)
        user_ids = list(config.AUTHORIZED_USERS.keys())
        user2_name = config.get_user_name(user_ids[1]) if len(user_ids) > 1 else "Пользователь 2"
        title = f"⭐ Топ-10 {user2_name}:"
    
    if not movies:
        text = "📋 Топ пуст"
    else:
        text = f"{title}\n\n"
        for i, movie in enumerate(movies, 1):
            # Проверяем наличие ключа в Row объекте
            if 'avg_rating' in dict(movie):
                rating = movie['avg_rating']
            else:
                rating = movie['rating']
            text += f"{i}. {movie['title']} - {rating:.1f}/10\n"
    
    keyboard = back_button("movies_top")
    await query.edit_message_text(text, reply_markup=keyboard)


async def movies_random(update: Update, context) -> None:
    """Случайный фильм."""
    query = update.callback_query
    await query.answer()
    
    movie = database.get_random_movie(exclude_series=True)
    
    if not movie:
        await query.edit_message_text("❌ Нет доступных фильмов")
        return
    
    # Используем функцию детального просмотра
    context.user_data['current_movie_id'] = movie['id']
    query.data = f"movie_{movie['id']}"
    await movie_detail(update, context)


async def movies_add_start(update: Update, context) -> None:
    """Начало добавления фильма."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("➕ Добавление фильма\n\nВведите название фильма:")
    return MOVIE_TITLE


async def movies_add_title(update: Update, context) -> None:
    """Обработка названия фильма."""
    title = update.message.text.strip()
    if not title:
        await update.message.reply_text("❌ Название не может быть пустым. Попробуйте еще раз:")
        return MOVIE_TITLE
    
    context.user_data['movie_title'] = title
    await update.message.reply_text("📝 Введите примечание (или /skip для пропуска):")
    return MOVIE_NOTE


async def movies_add_note(update: Update, context) -> None:
    """Обработка примечания фильма."""
    note = update.message.text.strip() if update.message.text != "/skip" else None
    context.user_data['movie_note'] = note
    
    # Показываем категории
    categories = database.get_movie_categories()
    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(cat['title'], callback_data=f"movie_cat_{cat['id']}")])
    keyboard.append([InlineKeyboardButton("➕ Создать новую категорию", callback_data="movie_cat_new")])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="movies_menu")])
    
    await update.message.reply_text(
        "📁 Выберите категорию:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return MOVIE_CATEGORY


async def movies_add_category(update: Update, context) -> None:
    """Обработка выбора категории."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "movie_cat_new":
        await query.edit_message_text("📁 Введите название новой категории:")
        context.user_data['movie_waiting_new_category'] = True
        return MOVIE_CATEGORY
    
    category_id = int(query.data.split("_")[-1])
    title = context.user_data['movie_title']
    note = context.user_data.get('movie_note')
    
    movie_id = database.create_movie(title, note, category_id)
    
    await query.edit_message_text(f"✅ Фильм '{title}' добавлен!")
    await movies_menu(update, context)
    return ConversationHandler.END


async def movies_add_new_category(update: Update, context) -> None:
    """Создание новой категории и добавление фильма."""
    category_title = update.message.text.strip()
    if not category_title:
        await update.message.reply_text("❌ Название категории не может быть пустым. Попробуйте еще раз:")
        return MOVIE_CATEGORY
    
    try:
        category_id = database.create_movie_category(category_title)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
        return MOVIE_CATEGORY
    
    title = context.user_data['movie_title']
    note = context.user_data.get('movie_note')
    
    movie_id = database.create_movie(title, note, category_id)
    
    await update.message.reply_text(f"✅ Фильм '{title}' добавлен в категорию '{category_title}'!")
    await movies_menu(update, context)
    return ConversationHandler.END


async def movies_add_cancel(update: Update, context) -> None:
    """Отмена добавления фильма."""
    context.user_data.clear()
    await update.message.reply_text("❌ Добавление отменено")
    return ConversationHandler.END


async def movie_watched(update: Update, context) -> None:
    """Отметить фильм как просмотренный."""
    query = update.callback_query
    await query.answer()
    
    movie_id = int(query.data.split("_")[-1])
    database.mark_movie_watched(movie_id)
    
    # Начинаем процесс оценки
    context.user_data['rating_movie_id'] = movie_id
    context.user_data['rating_user'] = 1
    
    user1_name = config.get_user_name(list(config.AUTHORIZED_USERS.keys())[0]) or "Пользователь 1"
    keyboard = rating_keyboard("rate_movie_", movie_id, 1)
    
    await query.edit_message_text(
        f"⭐ Оцените фильм ({user1_name}):",
        reply_markup=keyboard
    )


async def movie_rating(update: Update, context) -> None:
    """Обработка оценки фильма."""
    query = update.callback_query
    await query.answer()
    
    if "cancel" in query.data:
        await query.edit_message_text("❌ Оценка отменена")
        return
    
    parts = query.data.split("_")
    movie_id = int(parts[2])
    user_num = int(parts[3].replace("user", ""))
    rating = int(parts[4])
    
    database.set_movie_rating(movie_id, user_num, rating)
    
    # Проверяем, нужно ли оценить второму пользователю
    user_ids = list(config.AUTHORIZED_USERS.keys())
    if len(user_ids) > 1 and user_num == 1:
        user2_name = config.get_user_name(user_ids[1]) or "Пользователь 2"
        context.user_data['rating_user'] = 2
        keyboard = rating_keyboard("rate_movie_", movie_id, 2)
        await query.edit_message_text(
            f"⭐ Оцените фильм ({user2_name}):",
            reply_markup=keyboard
        )
    else:
        await query.edit_message_text("✅ Оценка сохранена!")
        # Показываем детальный просмотр
        query.data = f"movie_{movie_id}"
        await movie_detail(update, context)


def register_handlers(application: Application) -> None:
    """Регистрация обработчиков раздела фильмы."""
    # ConversationHandler для добавления фильма
    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(movies_add_start, pattern="^movies_add$")],
        states={
            MOVIE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, movies_add_title)],
            MOVIE_NOTE: [MessageHandler(filters.TEXT, movies_add_note)],
            MOVIE_CATEGORY: [
                CallbackQueryHandler(movies_add_category, pattern="^movie_cat_\\d+$"),
                MessageHandler(filters.TEXT, movies_add_new_category)
            ]
        },
        fallbacks=[CommandHandler("cancel", movies_add_cancel)]
    )
    
    application.add_handler(add_conv)
    application.add_handler(CallbackQueryHandler(movies_menu, pattern="^movies_menu$"))
    application.add_handler(CallbackQueryHandler(movies_pending_menu, pattern="^movies_pending$"))
    application.add_handler(CallbackQueryHandler(movies_pending_list, pattern="^movies_pending_(all|cat_\\d+)$"))
    application.add_handler(CallbackQueryHandler(movie_detail, pattern="^movie_\\d+$"))
    application.add_handler(CallbackQueryHandler(movies_watched_menu, pattern="^movies_watched$"))
    application.add_handler(CallbackQueryHandler(movies_watched_list, pattern="^movies_watched_all$"))
    application.add_handler(CallbackQueryHandler(movies_top_menu, pattern="^movies_top$"))
    application.add_handler(CallbackQueryHandler(movies_top_show, pattern="^movies_top_(all|user[12])$"))
    application.add_handler(CallbackQueryHandler(movies_random, pattern="^movies_random$"))
    application.add_handler(CallbackQueryHandler(movie_watched, pattern="^movie_watched_\\d+$"))
    application.add_handler(CallbackQueryHandler(movie_rating, pattern="^rate_movie_"))

