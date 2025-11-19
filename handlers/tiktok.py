"""
Обработчики для раздела "Тренды TikTok".
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, ConversationHandler, filters
import database
from keyboards import list_keyboard, back_button

TIKTOK_TITLE, TIKTOK_VIDEO = range(2)


async def tiktok_menu(update: Update, context) -> None:
    """Меню раздела TikTok."""
    keyboard = [
        [InlineKeyboardButton("📋 Надо снять", callback_data="tiktok_todo")],
        [InlineKeyboardButton("✅ Снятые", callback_data="tiktok_done")],
        [InlineKeyboardButton("➕ Добавить тренд", callback_data="tiktok_add")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text("🎵 Раздел: Тренды TikTok\n\nВыберите действие:", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("🎵 Раздел: Тренды TikTok\n\nВыберите действие:", reply_markup=reply_markup)


async def tiktok_todo_list(update: Update, context) -> None:
    """Список трендов, которые надо снять."""
    query = update.callback_query
    await query.answer()
    
    trends = database.get_tiktok_trends(status='todo')
    
    if not trends:
        text = "📋 Список пуст"
        keyboard = back_button("tiktok_menu")
    else:
        text = f"📋 Надо снять ({len(trends)}):\n\n"
        for i, trend in enumerate(trends[:10], 1):
            text += f"{i}. {trend['title']}\n"
        
        if len(trends) > 10:
            text += f"\n... и еще {len(trends) - 10}"
        
        keyboard = list_keyboard(
            trends,
            page=0,
            items_per_page=10,
            callback_prefix="tiktok_",
            back_callback="tiktok_menu"
        )
    
    await query.edit_message_text(text, reply_markup=keyboard)


async def tiktok_done_list(update: Update, context) -> None:
    """Список снятых трендов."""
    query = update.callback_query
    await query.answer()
    
    trends = database.get_tiktok_trends(status='done')
    
    if not trends:
        text = "📋 Список пуст"
        keyboard = back_button("tiktok_menu")
    else:
        text = f"✅ Снятые ({len(trends)}):\n\n"
        for i, trend in enumerate(trends[:10], 1):
            text += f"{i}. {trend['title']}\n"
        
        if len(trends) > 10:
            text += f"\n... и еще {len(trends) - 10}"
        
        keyboard = list_keyboard(
            trends,
            page=0,
            items_per_page=10,
            callback_prefix="tiktok_",
            back_callback="tiktok_menu"
        )
    
    await query.edit_message_text(text, reply_markup=keyboard)


async def tiktok_detail(update: Update, context) -> None:
    """Детальный просмотр тренда TikTok."""
    query = update.callback_query
    await query.answer()
    
    trend_id = int(query.data.split("_")[1])
    trend = database.get_tiktok_trend_by_id(trend_id)
    
    if not trend:
        await query.edit_message_text("❌ Тренд не найден")
        return
    
    text = f"🎵 {trend['title']}\n\n"
    text += f"📊 Статус: {'✅ Снято' if trend['status'] == 'done' else '⏳ Надо снять'}\n"
    
    keyboard = []
    if trend['status'] == 'todo':
        keyboard.append([InlineKeyboardButton("✅ Выполнено", callback_data=f"tiktok_done_{trend_id}")])
    keyboard.append([InlineKeyboardButton("🗑 Удалить", callback_data=f"tiktok_delete_{trend_id}")])
    
    back_callback = "tiktok_todo" if trend['status'] == 'todo' else "tiktok_done"
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=back_callback)])
    
    try:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        
        # Если есть видео, отправляем его отдельным сообщением
        if trend['video_file_id']:
            await query.message.reply_video(trend['video_file_id'])
    except Exception as e:
        # Если сообщение содержит видео, используем reply_text
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        if trend['video_file_id']:
            await query.message.reply_video(trend['video_file_id'])


async def tiktok_done(update: Update, context) -> None:
    """Отметить тренд как выполненный."""
    query = update.callback_query
    await query.answer()
    
    trend_id = int(query.data.split("_")[-1])
    database.mark_tiktok_trend_done(trend_id)
    
    try:
        await query.edit_message_text("✅ Тренд отмечен как выполненный!")
    except:
        await query.message.reply_text("✅ Тренд отмечен как выполненный!")


async def tiktok_delete(update: Update, context) -> None:
    """Удалить тренд TikTok."""
    query = update.callback_query
    await query.answer()
    
    trend_id = int(query.data.split("_")[-1])
    trend = database.get_tiktok_trend_by_id(trend_id)
    
    if not trend:
        await query.edit_message_text("❌ Тренд не найден")
        return
    
    database.delete_tiktok_trend(trend_id)
    
    try:
        await query.edit_message_text(f"✅ Тренд '{trend['title']}' удален!")
    except:
        await query.message.reply_text(f"✅ Тренд '{trend['title']}' удален!")
    
    # Возвращаемся в соответствующий список
    back_callback = "tiktok_todo" if trend['status'] == 'todo' else "tiktok_done"
    if back_callback == "tiktok_todo":
        await tiktok_todo_list(update, context)
    else:
        await tiktok_done_list(update, context)


async def tiktok_add_start(update: Update, context) -> None:
    """Начало добавления тренда."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("➕ Добавление тренда\n\nВведите название тренда:")
    return TIKTOK_TITLE


async def tiktok_add_title(update: Update, context) -> None:
    """Обработка названия тренда."""
    title = update.message.text.strip()
    if not title:
        await update.message.reply_text("❌ Название не может быть пустым. Попробуйте еще раз:")
        return TIKTOK_TITLE
    
    context.user_data['tiktok_title'] = title
    await update.message.reply_text("🎥 Прикрепите видео (или отправьте /skip для пропуска):")
    return TIKTOK_VIDEO


async def tiktok_add_video(update: Update, context) -> None:
    """Обработка видео тренда."""
    video_file_id = None
    
    if update.message.video:
        video_file_id = update.message.video.file_id
    elif update.message.document and update.message.document.mime_type and 'video' in update.message.document.mime_type:
        video_file_id = update.message.document.file_id
    
    title = context.user_data['tiktok_title']
    trend_id = database.create_tiktok_trend(title, video_file_id)
    
    await update.message.reply_text(f"✅ Тренд '{title}' добавлен!")
    await tiktok_menu(update, context)
    return ConversationHandler.END


async def tiktok_add_skip(update: Update, context) -> None:
    """Пропуск видео."""
    title = context.user_data['tiktok_title']
    trend_id = database.create_tiktok_trend(title, None)
    
    await update.message.reply_text(f"✅ Тренд '{title}' добавлен!")
    await tiktok_menu(update, context)
    return ConversationHandler.END


async def tiktok_add_cancel(update: Update, context) -> None:
    """Отмена добавления тренда."""
    context.user_data.clear()
    await update.message.reply_text("❌ Добавление отменено")
    return ConversationHandler.END


def register_handlers(application: Application) -> None:
    """Регистрация обработчиков раздела TikTok."""
    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(tiktok_add_start, pattern="^tiktok_add$")],
        states={
            TIKTOK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tiktok_add_title)],
            TIKTOK_VIDEO: [
                MessageHandler(filters.VIDEO | filters.Document.VIDEO, tiktok_add_video),
                MessageHandler(filters.TEXT & filters.Regex("^/skip$"), tiktok_add_skip)
            ]
        },
        fallbacks=[CommandHandler("cancel", tiktok_add_cancel)]
    )
    
    application.add_handler(add_conv)
    application.add_handler(CallbackQueryHandler(tiktok_menu, pattern="^tiktok_menu$"))
    application.add_handler(CallbackQueryHandler(tiktok_todo_list, pattern="^tiktok_todo$"))
    application.add_handler(CallbackQueryHandler(tiktok_done_list, pattern="^tiktok_done$"))
    application.add_handler(CallbackQueryHandler(tiktok_detail, pattern="^tiktok_\\d+$"))
    application.add_handler(CallbackQueryHandler(tiktok_done, pattern="^tiktok_done_\\d+$"))
    application.add_handler(CallbackQueryHandler(tiktok_delete, pattern="^tiktok_delete_\\d+$"))

