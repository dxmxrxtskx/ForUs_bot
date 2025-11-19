"""
Обработчики для раздела "Поездки".
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, ConversationHandler, filters
import database
from keyboards import list_keyboard, back_button

TRIP_TITLE, TRIP_NOTE, TRIP_CATEGORY = range(3)
EDIT_TRIP_TITLE, EDIT_TRIP_NOTE = range(3, 5)


async def trips_menu(update: Update, context) -> None:
    """Меню раздела поездки."""
    categories = database.get_trip_categories()
    
    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(f"📍 {cat['title']}", callback_data=f"trips_cat_{cat['id']}")])
    
    keyboard.append([InlineKeyboardButton("➕ Добавить", callback_data="trips_add")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text("✈️ Раздел: Поездки\n\nВыберите категорию:", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("✈️ Раздел: Поездки\n\nВыберите категорию:", reply_markup=reply_markup)


async def trips_category_list(update: Update, context) -> None:
    """Список поездок в категории."""
    query = update.callback_query
    await query.answer()
    
    category_id = int(query.data.split("_")[-1])
    trips = database.get_trips(category_id=category_id)
    category = next((c for c in database.get_trip_categories() if c['id'] == category_id), None)
    
    if not trips:
        text = f"📋 Категория '{category['title']}' пуста"
        keyboard = back_button("trips_menu")
    else:
        text = f"📍 {category['title']} ({len(trips)}):\n\n"
        for i, trip in enumerate(trips[:10], 1):
            status = "✅" if trip['visited'] else "⏳"
            text += f"{i}. {status} {trip['title']}\n"
        
        if len(trips) > 10:
            text += f"\n... и еще {len(trips) - 10}"
        
        keyboard = list_keyboard(
            trips,
            page=0,
            items_per_page=10,
            callback_prefix="trip_",
            back_callback="trips_menu"
        )
    
    await query.edit_message_text(text, reply_markup=keyboard)


async def trip_detail(update: Update, context) -> None:
    """Детальный просмотр поездки."""
    query = update.callback_query
    await query.answer()
    
    trip_id = int(query.data.split("_")[1])
    trip = database.get_trip_by_id(trip_id)
    
    if not trip:
        await query.edit_message_text("❌ Поездка не найдена")
        return
    
    text = f"✈️ {trip['title']}\n\n"
    if trip['note']:
        text += f"📝 {trip['note']}\n\n"
    text += f"📁 Категория: {trip['category_title']}\n"
    text += f"📊 Статус: {'✅ Посещено' if trip['visited'] else '⏳ Не посещено'}\n"
    
    keyboard = []
    if not trip['visited']:
        keyboard.append([InlineKeyboardButton("✅ Посещено", callback_data=f"trip_visited_{trip_id}")])
    keyboard.append([InlineKeyboardButton("✏️ Редактировать", callback_data=f"trip_edit_{trip_id}")])
    keyboard.append([InlineKeyboardButton("🗑 Удалить", callback_data=f"trip_delete_{trip_id}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f"trips_cat_{trip['category_id']}")])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def trip_visited(update: Update, context) -> None:
    """Отметить поездку как посещенную."""
    query = update.callback_query
    await query.answer()
    
    trip_id = int(query.data.split("_")[-1])
    database.mark_trip_visited(trip_id)
    
    await query.edit_message_text("✅ Поездка отмечена как посещенная!")
    query.data = f"trip_{trip_id}"
    await trip_detail(update, context)


async def trip_delete(update: Update, context) -> None:
    """Удалить поездку."""
    query = update.callback_query
    await query.answer()
    
    trip_id = int(query.data.split("_")[-1])
    trip = database.get_trip_by_id(trip_id)
    
    if not trip:
        await query.edit_message_text("❌ Поездка не найдена")
        return
    
    database.delete_trip(trip_id)
    await query.edit_message_text(f"✅ Поездка '{trip['title']}' удалена!")
    await trips_category_list(update, context)


async def trips_add_start(update: Update, context) -> None:
    """Начало добавления поездки."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("➕ Добавление поездки\n\nВведите название поездки:")
    return TRIP_TITLE


async def trips_add_title(update: Update, context) -> None:
    """Обработка названия поездки."""
    title = update.message.text.strip()
    if not title:
        await update.message.reply_text("❌ Название не может быть пустым. Попробуйте еще раз:")
        return TRIP_TITLE
    
    context.user_data['trip_title'] = title
    await update.message.reply_text("📝 Введите примечание (или /skip для пропуска):")
    return TRIP_NOTE


async def trips_add_note(update: Update, context) -> None:
    """Обработка примечания поездки."""
    note = update.message.text.strip() if update.message.text != "/skip" else None
    context.user_data['trip_note'] = note
    
    categories = database.get_trip_categories()
    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(cat['title'], callback_data=f"trip_cat_{cat['id']}")])
    keyboard.append([InlineKeyboardButton("➕ Создать новую категорию", callback_data="trip_cat_new")])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="trips_menu")])
    
    await update.message.reply_text(
        "📁 Выберите категорию:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TRIP_CATEGORY


async def trips_add_category(update: Update, context) -> None:
    """Обработка выбора категории."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "trip_cat_new":
        await query.edit_message_text("📁 Введите название новой категории:")
        context.user_data['trip_waiting_new_category'] = True
        return TRIP_CATEGORY
    
    category_id = int(query.data.split("_")[-1])
    title = context.user_data['trip_title']
    note = context.user_data.get('trip_note')
    
    trip_id = database.create_trip(title, note, category_id)
    
    await query.edit_message_text(f"✅ Поездка '{title}' добавлена!")
    await trips_menu(update, context)
    return ConversationHandler.END


async def trips_add_new_category(update: Update, context) -> None:
    """Создание новой категории и добавление поездки."""
    category_title = update.message.text.strip()
    if not category_title:
        await update.message.reply_text("❌ Название категории не может быть пустым. Попробуйте еще раз:")
        return TRIP_CATEGORY
    
    try:
        category_id = database.create_trip_category(category_title)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
        return TRIP_CATEGORY
    
    title = context.user_data['trip_title']
    note = context.user_data.get('trip_note')
    
    trip_id = database.create_trip(title, note, category_id)
    
    await update.message.reply_text(f"✅ Поездка '{title}' добавлена в категорию '{category_title}'!")
    await trips_menu(update, context)
    return ConversationHandler.END


async def trips_add_cancel(update: Update, context) -> None:
    """Отмена добавления поездки."""
    context.user_data.clear()
    await update.message.reply_text("❌ Добавление отменено")
    return ConversationHandler.END


def register_handlers(application: Application) -> None:
    """Регистрация обработчиков раздела поездки."""
    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(trips_add_start, pattern="^trips_add$")],
        states={
            TRIP_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, trips_add_title)],
            TRIP_NOTE: [MessageHandler(filters.TEXT, trips_add_note)],
            TRIP_CATEGORY: [
                CallbackQueryHandler(trips_add_category, pattern="^trip_cat_\\d+$"),
                MessageHandler(filters.TEXT, trips_add_new_category)
            ]
        },
        fallbacks=[CommandHandler("cancel", trips_add_cancel)]
    )
    
    application.add_handler(add_conv)
    application.add_handler(CallbackQueryHandler(trips_menu, pattern="^trips_menu$"))
    application.add_handler(CallbackQueryHandler(trips_category_list, pattern="^trips_cat_\\d+$"))
    application.add_handler(CallbackQueryHandler(trip_detail, pattern="^trip_\\d+$"))
    application.add_handler(CallbackQueryHandler(trip_visited, pattern="^trip_visited_\\d+$"))
    application.add_handler(CallbackQueryHandler(trip_delete, pattern="^trip_delete_\\d+$"))

