"""
Обработчики для раздела "Sexual".
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, ConversationHandler, filters
import database
from keyboards import list_keyboard, back_button

SEXUAL_TITLE, SEXUAL_LINK, SEXUAL_DESC = range(3)
EDIT_SEXUAL_TITLE, EDIT_SEXUAL_LINK, EDIT_SEXUAL_DESC = range(3, 6)


async def sexual_menu(update: Update, context) -> None:
    """Меню раздела sexual."""
    items = database.get_sexual_items()
    
    keyboard = []
    if items:
        keyboard.append([InlineKeyboardButton("📋 Список", callback_data="sexual_list")])
    keyboard.append([InlineKeyboardButton("➕ Добавить", callback_data="sexual_add")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text("🔞 Раздел: Sexual\n\nВыберите действие:", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("🔞 Раздел: Sexual\n\nВыберите действие:", reply_markup=reply_markup)


async def sexual_list(update: Update, context) -> None:
    """Список записей sexual."""
    query = update.callback_query
    await query.answer()
    
    items = database.get_sexual_items()
    
    if not items:
        text = "📋 Список пуст"
        keyboard = back_button("sexual_menu")
    else:
        text = f"🔞 Записи ({len(items)}):\n\n"
        for i, item in enumerate(items[:10], 1):
            text += f"{i}. {item['title']}\n"
        
        if len(items) > 10:
            text += f"\n... и еще {len(items) - 10}"
        
        keyboard = list_keyboard(
            items,
            page=0,
            items_per_page=10,
            callback_prefix="sexual_",
            back_callback="sexual_menu"
        )
    
    await query.edit_message_text(text, reply_markup=keyboard)


async def sexual_detail(update: Update, context) -> None:
    """Детальный просмотр записи sexual."""
    query = update.callback_query
    await query.answer()
    
    item_id = int(query.data.split("_")[1])
    item = database.get_sexual_item_by_id(item_id)
    
    if not item:
        await query.edit_message_text("❌ Запись не найдена")
        return
    
    text = f"🔞 {item['title']}\n\n"
    if item['link']:
        text += f"🔗 {item['link']}\n\n"
    if item['description']:
        text += f"📝 {item['description']}\n"
    
    keyboard = [
        [InlineKeyboardButton("✏️ Редактировать", callback_data=f"sexual_edit_{item_id}")],
        [InlineKeyboardButton("🗑 Удалить", callback_data=f"sexual_delete_{item_id}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="sexual_list")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def sexual_delete(update: Update, context) -> None:
    """Удалить запись sexual."""
    query = update.callback_query
    await query.answer()
    
    item_id = int(query.data.split("_")[-1])
    item = database.get_sexual_item_by_id(item_id)
    
    if not item:
        await query.edit_message_text("❌ Запись не найдена")
        return
    
    database.delete_sexual_item(item_id)
    await query.edit_message_text(f"✅ Запись '{item['title']}' удалена!")
    await sexual_list(update, context)


async def sexual_add_start(update: Update, context) -> None:
    """Начало добавления записи sexual."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("➕ Добавление записи\n\nВведите название:")
    return SEXUAL_TITLE


async def sexual_add_title(update: Update, context) -> None:
    """Обработка названия записи."""
    title = update.message.text.strip()
    if not title:
        await update.message.reply_text("❌ Название не может быть пустым. Попробуйте еще раз:")
        return SEXUAL_TITLE
    
    context.user_data['sexual_title'] = title
    await update.message.reply_text("🔗 Введите ссылку (или /skip для пропуска):")
    return SEXUAL_LINK


async def sexual_add_link(update: Update, context) -> None:
    """Обработка ссылки записи."""
    link = update.message.text.strip() if update.message.text != "/skip" else None
    context.user_data['sexual_link'] = link
    await update.message.reply_text("📝 Введите описание (или /skip для пропуска):")
    return SEXUAL_DESC


async def sexual_add_desc(update: Update, context) -> None:
    """Обработка описания записи."""
    desc = update.message.text.strip() if update.message.text != "/skip" else None
    title = context.user_data['sexual_title']
    link = context.user_data.get('sexual_link')
    
    item_id = database.create_sexual_item(title, link, desc)
    
    await update.message.reply_text(f"✅ Запись '{title}' добавлена!")
    await sexual_menu(update, context)
    return ConversationHandler.END


async def sexual_add_cancel(update: Update, context) -> None:
    """Отмена добавления записи."""
    context.user_data.clear()
    await update.message.reply_text("❌ Добавление отменено")
    return ConversationHandler.END


def register_handlers(application: Application) -> None:
    """Регистрация обработчиков раздела sexual."""
    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(sexual_add_start, pattern="^sexual_add$")],
        states={
            SEXUAL_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sexual_add_title)],
            SEXUAL_LINK: [MessageHandler(filters.TEXT, sexual_add_link)],
            SEXUAL_DESC: [MessageHandler(filters.TEXT, sexual_add_desc)]
        },
        fallbacks=[CommandHandler("cancel", sexual_add_cancel)]
    )
    
    application.add_handler(add_conv)
    application.add_handler(CallbackQueryHandler(sexual_menu, pattern="^sexual_menu$"))
    application.add_handler(CallbackQueryHandler(sexual_list, pattern="^sexual_list$"))
    application.add_handler(CallbackQueryHandler(sexual_detail, pattern="^sexual_\\d+$"))
    application.add_handler(CallbackQueryHandler(sexual_delete, pattern="^sexual_delete_\\d+$"))

