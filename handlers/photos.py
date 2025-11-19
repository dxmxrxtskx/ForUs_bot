"""
Обработчики для раздела "Фотографии".
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, ConversationHandler, filters
import database
from keyboards import list_keyboard, back_button

PHOTO_TITLE, PHOTO_LINK, PHOTO_DESC = range(3)
EDIT_PHOTO_TITLE, EDIT_PHOTO_LINK, EDIT_PHOTO_DESC = range(3, 6)


async def photos_menu(update: Update, context) -> None:
    """Меню раздела фотографии."""
    categories = database.get_photo_categories()
    
    keyboard = []
    if categories:
        keyboard.append([InlineKeyboardButton("📋 Список категорий", callback_data="photos_list")])
    keyboard.append([InlineKeyboardButton("➕ Добавить категорию", callback_data="photos_add")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text("📸 Раздел: Фотографии\n\nВыберите действие:", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("📸 Раздел: Фотографии\n\nВыберите действие:", reply_markup=reply_markup)


async def photos_list(update: Update, context) -> None:
    """Список категорий фотографий."""
    query = update.callback_query
    await query.answer()
    
    categories = database.get_photo_categories()
    
    if not categories:
        text = "📋 Список пуст"
        keyboard = back_button("photos_menu")
    else:
        text = f"📸 Категории фотографий ({len(categories)}):\n\n"
        for i, cat in enumerate(categories[:10], 1):
            text += f"{i}. {cat['title']}\n"
        
        if len(categories) > 10:
            text += f"\n... и еще {len(categories) - 10}"
        
        keyboard = list_keyboard(
            categories,
            page=0,
            items_per_page=10,
            callback_prefix="photo_cat_",
            back_callback="photos_menu"
        )
    
    await query.edit_message_text(text, reply_markup=keyboard)


async def photo_category_detail(update: Update, context) -> None:
    """Детальный просмотр категории фотографий."""
    query = update.callback_query
    await query.answer()
    
    category_id = int(query.data.split("_")[-1])
    category = database.get_photo_category_by_id(category_id)
    
    if not category:
        await query.edit_message_text("❌ Категория не найдена")
        return
    
    text = f"📸 {category['title']}\n\n"
    if category['link']:
        text += f"🔗 Ссылка: {category['link']}\n\n"
    if category['description']:
        text += f"📝 {category['description']}\n"
    
    keyboard = [
        [InlineKeyboardButton("✏️ Редактировать", callback_data=f"photo_cat_edit_{category_id}")],
        [InlineKeyboardButton("🗑 Удалить", callback_data=f"photo_cat_delete_{category_id}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="photos_list")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def photo_category_delete(update: Update, context) -> None:
    """Удалить категорию фотографий."""
    query = update.callback_query
    await query.answer()
    
    category_id = int(query.data.split("_")[-1])
    category = database.get_photo_category_by_id(category_id)
    
    if not category:
        await query.edit_message_text("❌ Категория не найдена")
        return
    
    database.delete_photo_category(category_id)
    await query.edit_message_text(f"✅ Категория '{category['title']}' удалена!")
    await photos_list(update, context)


async def photos_add_start(update: Update, context) -> None:
    """Начало добавления категории фотографий."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("➕ Добавление категории\n\nВведите название категории:")
    return PHOTO_TITLE


async def photos_add_title(update: Update, context) -> None:
    """Обработка названия категории."""
    title = update.message.text.strip()
    if not title:
        await update.message.reply_text("❌ Название не может быть пустым. Попробуйте еще раз:")
        return PHOTO_TITLE
    
    context.user_data['photo_title'] = title
    await update.message.reply_text("🔗 Введите ссылку (или /skip для пропуска):")
    return PHOTO_LINK


async def photos_add_link(update: Update, context) -> None:
    """Обработка ссылки категории."""
    link = update.message.text.strip() if update.message.text != "/skip" else None
    context.user_data['photo_link'] = link
    await update.message.reply_text("📝 Введите описание (или /skip для пропуска):")
    return PHOTO_DESC


async def photos_add_desc(update: Update, context) -> None:
    """Обработка описания категории."""
    desc = update.message.text.strip() if update.message.text != "/skip" else None
    title = context.user_data['photo_title']
    link = context.user_data.get('photo_link')
    
    category_id = database.create_photo_category(title, link, desc)
    
    await update.message.reply_text(f"✅ Категория '{title}' добавлена!")
    await photos_menu(update, context)
    return ConversationHandler.END


async def photos_add_cancel(update: Update, context) -> None:
    """Отмена добавления категории."""
    context.user_data.clear()
    await update.message.reply_text("❌ Добавление отменено")
    return ConversationHandler.END


def register_handlers(application: Application) -> None:
    """Регистрация обработчиков раздела фотографии."""
    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(photos_add_start, pattern="^photos_add$")],
        states={
            PHOTO_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, photos_add_title)],
            PHOTO_LINK: [MessageHandler(filters.TEXT, photos_add_link)],
            PHOTO_DESC: [MessageHandler(filters.TEXT, photos_add_desc)]
        },
        fallbacks=[CommandHandler("cancel", photos_add_cancel)]
    )
    
    application.add_handler(add_conv)
    application.add_handler(CallbackQueryHandler(photos_menu, pattern="^photos_menu$"))
    application.add_handler(CallbackQueryHandler(photos_list, pattern="^photos_list$"))
    application.add_handler(CallbackQueryHandler(photo_category_detail, pattern="^photo_cat_\\d+$"))
    application.add_handler(CallbackQueryHandler(photo_category_delete, pattern="^photo_cat_delete_\\d+$"))

