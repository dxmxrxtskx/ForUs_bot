"""
Обработчики для раздела "Игры".
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, ConversationHandler, filters
import database
import config
from keyboards import list_keyboard, back_button, rating_keyboard

GAME_TITLE, GAME_NOTE, GAME_GENRE = range(3)
EDIT_GAME_TITLE, EDIT_GAME_NOTE, EDIT_GAME_GENRE = range(3, 6)
RATING_GAME_USER1, RATING_GAME_USER2 = range(6, 8)


async def games_menu(update: Update, context) -> None:
    """Меню раздела игры."""
    keyboard = [
        [InlineKeyboardButton("📋 Ожидающие", callback_data="games_pending")],
        [InlineKeyboardButton("✅ Пройденные", callback_data="games_done")],
        [InlineKeyboardButton("🏆 Топ-10", callback_data="games_top")],
        [InlineKeyboardButton("🎲 Случайная игра", callback_data="games_random")],
        [InlineKeyboardButton("➕ Добавить игру", callback_data="games_add")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text("🎮 Раздел: Игры\n\nВыберите действие:", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("🎮 Раздел: Игры\n\nВыберите действие:", reply_markup=reply_markup)


async def games_pending_menu(update: Update, context) -> None:
    """Подменю ожидающих игр."""
    query = update.callback_query
    await query.answer()
    
    genres = database.get_game_genres()
    keyboard = [
        [InlineKeyboardButton("📋 Общий список", callback_data="games_pending_all")]
    ]
    
    for genre in genres:
        keyboard.append([InlineKeyboardButton(f"📁 {genre}", callback_data=f"games_pending_genre_{genre}")])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="games_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("📋 Ожидающие игры\n\nВыберите фильтр:", reply_markup=reply_markup)


async def games_pending_list(update: Update, context) -> None:
    """Список ожидающих игр."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == "games_pending_all":
        games = database.get_games(status='pending')
        genre = None
    else:
        genre = data.split("_")[-1]
        games = database.get_games(status='pending', genre=genre)
    
    if not games:
        text = "📋 Список пуст"
        keyboard = back_button("games_pending")
    else:
        text = f"📋 Ожидающие игры ({len(games)}):\n\n"
        for i, game in enumerate(games[:10], 1):
            text += f"{i}. {game['title']}"
            if game['genre']:
                text += f" ({game['genre']})"
            text += "\n"
        
        if len(games) > 10:
            text += f"\n... и еще {len(games) - 10}"
        
        keyboard = list_keyboard(
            games,
            page=0,
            items_per_page=10,
            callback_prefix="game_",
            back_callback="games_pending"
        )
    
    await query.edit_message_text(text, reply_markup=keyboard)


async def game_detail(update: Update, context) -> None:
    """Детальный просмотр игры."""
    query = update.callback_query
    await query.answer()
    
    game_id = int(query.data.split("_")[1])
    game = database.get_game_by_id(game_id)
    
    if not game:
        await query.edit_message_text("❌ Игра не найдена")
        return
    
    text = f"🎮 {game['title']}\n\n"
    if game['note']:
        text += f"📝 {game['note']}\n\n"
    if game['genre']:
        text += f"📁 Жанр: {game['genre']}\n"
    
    if game['status'] == 'done':
        text += f"✅ Пройдена\n"
        if game['user1_rating']:
            user1_name = config.get_user_name(list(config.AUTHORIZED_USERS.keys())[0]) or "Пользователь 1"
            text += f"⭐ {user1_name}: {game['user1_rating']}/10\n"
        if game['user2_rating']:
            user2_name = config.get_user_name(list(config.AUTHORIZED_USERS.keys())[1]) if len(config.AUTHORIZED_USERS) > 1 else "Пользователь 2"
            text += f"⭐ {user2_name}: {game['user2_rating']}/10\n"
    else:
        text += "⏳ Ожидает прохождения\n"
    
    keyboard = []
    if game['status'] == 'pending':
        keyboard.append([InlineKeyboardButton("✅ Пройдено", callback_data=f"game_done_{game_id}")])
    keyboard.append([InlineKeyboardButton("✏️ Редактировать", callback_data=f"game_edit_{game_id}")])
    keyboard.append([InlineKeyboardButton("🗑 Удалить", callback_data=f"game_delete_{game_id}")])
    
    back_callback = "games_pending" if game['status'] == 'pending' else "games_done"
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=back_callback)])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def games_done_menu(update: Update, context) -> None:
    """Меню пройденных игр."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📋 Общий список", callback_data="games_done_all")],
        [InlineKeyboardButton("🏆 Топ-10", callback_data="games_top")],
        [InlineKeyboardButton("◀️ Назад", callback_data="games_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("✅ Пройденные игры\n\nВыберите действие:", reply_markup=reply_markup)


async def games_done_list(update: Update, context) -> None:
    """Список пройденных игр."""
    query = update.callback_query
    await query.answer()
    
    games = database.get_games(status='done')
    
    if not games:
        text = "📋 Список пуст"
        keyboard = back_button("games_done")
    else:
        text = f"✅ Пройденные игры ({len(games)}):\n\n"
        for i, game in enumerate(games[:10], 1):
            rating_text = ""
            if game['user1_rating'] and game['user2_rating']:
                avg = (game['user1_rating'] + game['user2_rating']) / 2
                rating_text = f" - {avg:.1f}/10"
            text += f"{i}. {game['title']}{rating_text}\n"
        
        if len(games) > 10:
            text += f"\n... и еще {len(games) - 10}"
        
        keyboard = list_keyboard(
            games,
            page=0,
            items_per_page=10,
            callback_prefix="game_",
            back_callback="games_done"
        )
    
    await query.edit_message_text(text, reply_markup=keyboard)


async def games_top_menu(update: Update, context) -> None:
    """Меню топ-10 игр."""
    query = update.callback_query
    await query.answer()
    
    user_ids = list(config.AUTHORIZED_USERS.keys())
    user1_name = config.get_user_name(user_ids[0]) or "Пользователь 1"
    user2_name = config.get_user_name(user_ids[1]) if len(user_ids) > 1 else "Пользователь 2"
    
    keyboard = [
        [InlineKeyboardButton("🏆 Общий топ", callback_data="games_top_all")],
        [InlineKeyboardButton(f"⭐ {user1_name}", callback_data="games_top_user1")],
        [InlineKeyboardButton(f"⭐ {user2_name}", callback_data="games_top_user2")],
        [InlineKeyboardButton("◀️ Назад", callback_data="games_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("🏆 Топ-10 игр\n\nВыберите топ:", reply_markup=reply_markup)


async def games_top_show(update: Update, context) -> None:
    """Показать топ-10 игр."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == "games_top_all":
        games = database.get_games_top(limit=10, user_num=None)
        title = "🏆 Общий топ-10:"
    elif data == "games_top_user1":
        games = database.get_games_top(limit=10, user_num=1)
        user1_name = config.get_user_name(list(config.AUTHORIZED_USERS.keys())[0]) or "Пользователь 1"
        title = f"⭐ Топ-10 {user1_name}:"
    else:
        games = database.get_games_top(limit=10, user_num=2)
        user_ids = list(config.AUTHORIZED_USERS.keys())
        user2_name = config.get_user_name(user_ids[1]) if len(user_ids) > 1 else "Пользователь 2"
        title = f"⭐ Топ-10 {user2_name}:"
    
    if not games:
        text = "📋 Топ пуст"
    else:
        text = f"{title}\n\n"
        for i, game in enumerate(games, 1):
            # Проверяем наличие ключа в Row объекте
            if 'avg_rating' in dict(game):
                rating = game['avg_rating']
            else:
                rating = game['rating']
            text += f"{i}. {game['title']} - {rating:.1f}/10\n"
    
    keyboard = back_button("games_top")
    await query.edit_message_text(text, reply_markup=keyboard)


async def games_random(update: Update, context) -> None:
    """Случайная игра."""
    query = update.callback_query
    await query.answer()
    
    game = database.get_random_game()
    
    if not game:
        await query.edit_message_text("❌ Нет доступных игр")
        return
    
    query.data = f"game_{game['id']}"
    await game_detail(update, context)


async def game_done(update: Update, context) -> None:
    """Отметить игру как пройденную."""
    query = update.callback_query
    await query.answer()
    
    game_id = int(query.data.split("_")[-1])
    database.mark_game_done(game_id)
    
    # Начинаем процесс оценки
    context.user_data['rating_game_id'] = game_id
    context.user_data['rating_user'] = 1
    
    user1_name = config.get_user_name(list(config.AUTHORIZED_USERS.keys())[0]) or "Пользователь 1"
    keyboard = rating_keyboard("rate_game_", game_id, 1)
    
    await query.edit_message_text(
        f"⭐ Оцените игру ({user1_name}):",
        reply_markup=keyboard
    )


async def game_rating(update: Update, context) -> None:
    """Обработка оценки игры."""
    query = update.callback_query
    await query.answer()
    
    if "cancel" in query.data:
        await query.edit_message_text("❌ Оценка отменена")
        return
    
    parts = query.data.split("_")
    game_id = int(parts[2])
    user_num = int(parts[3].replace("user", ""))
    rating = int(parts[4])
    
    database.set_game_rating(game_id, user_num, rating)
    
    # Проверяем, нужно ли оценить второму пользователю
    user_ids = list(config.AUTHORIZED_USERS.keys())
    if len(user_ids) > 1 and user_num == 1:
        user2_name = config.get_user_name(user_ids[1]) or "Пользователь 2"
        context.user_data['rating_user'] = 2
        keyboard = rating_keyboard("rate_game_", game_id, 2)
        await query.edit_message_text(
            f"⭐ Оцените игру ({user2_name}):",
            reply_markup=keyboard
        )
    else:
        await query.edit_message_text("✅ Оценка сохранена!")
        query.data = f"game_{game_id}"
        await game_detail(update, context)


async def game_delete(update: Update, context) -> None:
    """Удалить игру."""
    query = update.callback_query
    await query.answer()
    
    game_id = int(query.data.split("_")[-1])
    game = database.get_game_by_id(game_id)
    
    if not game:
        await query.edit_message_text("❌ Игра не найдена")
        return
    
    database.delete_game(game_id)
    await query.edit_message_text(f"✅ Игра '{game['title']}' удалена!")
    
    back_callback = "games_pending" if game['status'] == 'pending' else "games_done"
    if back_callback == "games_pending":
        await games_pending_list(update, context)
    else:
        await games_done_list(update, context)


async def games_add_start(update: Update, context) -> None:
    """Начало добавления игры."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("➕ Добавление игры\n\nВведите название игры:")
    return GAME_TITLE


async def games_add_title(update: Update, context) -> None:
    """Обработка названия игры."""
    title = update.message.text.strip()
    if not title:
        await update.message.reply_text("❌ Название не может быть пустым. Попробуйте еще раз:")
        return GAME_TITLE
    
    context.user_data['game_title'] = title
    await update.message.reply_text("📝 Введите примечание (или /skip для пропуска):")
    return GAME_NOTE


async def games_add_note(update: Update, context) -> None:
    """Обработка примечания игры."""
    note = update.message.text.strip() if update.message.text != "/skip" else None
    context.user_data['game_note'] = note
    await update.message.reply_text("📁 Введите жанр (или /skip для пропуска):")
    return GAME_GENRE


async def games_add_genre(update: Update, context) -> None:
    """Обработка жанра игры."""
    genre = update.message.text.strip() if update.message.text != "/skip" else None
    title = context.user_data['game_title']
    note = context.user_data.get('game_note')
    
    game_id = database.create_game(title, note, genre)
    
    await update.message.reply_text(f"✅ Игра '{title}' добавлена!")
    await games_menu(update, context)
    return ConversationHandler.END


async def games_add_cancel(update: Update, context) -> None:
    """Отмена добавления игры."""
    context.user_data.clear()
    await update.message.reply_text("❌ Добавление отменено")
    return ConversationHandler.END


def register_handlers(application: Application) -> None:
    """Регистрация обработчиков раздела игры."""
    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(games_add_start, pattern="^games_add$")],
        states={
            GAME_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, games_add_title)],
            GAME_NOTE: [MessageHandler(filters.TEXT, games_add_note)],
            GAME_GENRE: [MessageHandler(filters.TEXT, games_add_genre)]
        },
        fallbacks=[CommandHandler("cancel", games_add_cancel)]
    )
    
    application.add_handler(add_conv)
    application.add_handler(CallbackQueryHandler(games_menu, pattern="^games_menu$"))
    application.add_handler(CallbackQueryHandler(games_pending_menu, pattern="^games_pending$"))
    application.add_handler(CallbackQueryHandler(games_pending_list, pattern="^games_pending_(all|genre_.+)$"))
    application.add_handler(CallbackQueryHandler(game_detail, pattern="^game_\\d+$"))
    application.add_handler(CallbackQueryHandler(games_done_menu, pattern="^games_done$"))
    application.add_handler(CallbackQueryHandler(games_done_list, pattern="^games_done_all$"))
    application.add_handler(CallbackQueryHandler(games_top_menu, pattern="^games_top$"))
    application.add_handler(CallbackQueryHandler(games_top_show, pattern="^games_top_(all|user[12])$"))
    application.add_handler(CallbackQueryHandler(games_random, pattern="^games_random$"))
    application.add_handler(CallbackQueryHandler(game_done, pattern="^game_done_\\d+$"))
    application.add_handler(CallbackQueryHandler(game_rating, pattern="^rate_game_"))
    application.add_handler(CallbackQueryHandler(game_delete, pattern="^game_delete_\\d+$"))

