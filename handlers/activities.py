"""
Обработчики для раздела "Активности".
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, ConversationHandler, filters
import database
from keyboards import list_keyboard, back_button, main_menu_button

ACTIVITY_TITLE, ACTIVITY_NOTE = range(2)
EDIT_ACTIVITY_TITLE, EDIT_ACTIVITY_NOTE = range(2, 4)


async def activities_menu(update: Update, context) -> None:
    """Меню раздела активности."""
    keyboard = [
        [InlineKeyboardButton("📋 Планируемые", callback_data="activities_planned")],
        [InlineKeyboardButton("✅ Выполненные", callback_data="activities_done")],
        [InlineKeyboardButton("➕ Добавить активность", callback_data="activities_add")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text("📝 Раздел: Активности\n\nВыберите действие:", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("📝 Раздел: Активности\n\nВыберите действие:", reply_markup=reply_markup)


async def activities_planned_list(update: Update, context) -> None:
    """Список планируемых активностей."""
    query = update.callback_query
    await query.answer()
    
    activities = database.get_activities(status='planned')
    
    if not activities:
        text = "📋 Список пуст"
        keyboard = back_button("activities_menu")
    else:
        text = f"📋 Планируемые ({len(activities)}):\n\n"
        for i, activity in enumerate(activities[:10], 1):
            text += f"{i}. {activity['title']}\n"
        
        if len(activities) > 10:
            text += f"\n... и еще {len(activities) - 10}"
        
        keyboard = list_keyboard(
            activities,
            page=0,
            items_per_page=10,
            callback_prefix="activity_",
            back_callback="activities_menu"
        )
    
    await query.edit_message_text(text, reply_markup=keyboard)


async def activities_done_list(update: Update, context) -> None:
    """Список выполненных активностей."""
    query = update.callback_query
    await query.answer()
    
    activities = database.get_activities(status='done')
    
    if not activities:
        text = "📋 Список пуст"
        keyboard = back_button("activities_menu")
    else:
        text = f"✅ Выполненные ({len(activities)}):\n\n"
        for i, activity in enumerate(activities[:10], 1):
            text += f"{i}. {activity['title']}\n"
        
        if len(activities) > 10:
            text += f"\n... и еще {len(activities) - 10}"
        
        keyboard = list_keyboard(
            activities,
            page=0,
            items_per_page=10,
            callback_prefix="activity_",
            back_callback="activities_menu"
        )
    
    await query.edit_message_text(text, reply_markup=keyboard)


async def activity_detail(update: Update, context) -> None:
    """Детальный просмотр активности."""
    query = update.callback_query
    await query.answer()
    
    activity_id = int(query.data.split("_")[1])
    activity = database.get_activity_by_id(activity_id)
    
    if not activity:
        await query.edit_message_text("❌ Активность не найдена")
        return
    
    text = f"📝 {activity['title']}\n\n"
    if activity['note']:
        text += f"📄 {activity['note']}\n\n"
    text += f"📊 Статус: {'✅ Выполнено' if activity['status'] == 'done' else '⏳ Планируется'}\n"
    
    keyboard = []
    if activity['status'] == 'planned':
        keyboard.append([InlineKeyboardButton("✅ Выполнено", callback_data=f"activity_done_{activity_id}")])
    keyboard.append([InlineKeyboardButton("✏️ Редактировать", callback_data=f"activity_edit_{activity_id}")])
    keyboard.append([InlineKeyboardButton("🗑 Удалить", callback_data=f"activity_delete_{activity_id}")])
    
    back_callback = "activities_planned" if activity['status'] == 'planned' else "activities_done"
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=back_callback)])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def activity_done(update: Update, context) -> None:
    """Отметить активность как выполненную."""
    query = update.callback_query
    await query.answer()
    
    activity_id = int(query.data.split("_")[-1])
    database.mark_activity_done(activity_id)
    
    await query.edit_message_text("✅ Активность отмечена как выполненная!")
    # Обновляем детальный просмотр
    query.data = f"activity_{activity_id}"
    await activity_detail(update, context)


async def activity_delete(update: Update, context) -> None:
    """Удалить активность."""
    query = update.callback_query
    await query.answer()
    
    activity_id = int(query.data.split("_")[-1])
    activity = database.get_activity_by_id(activity_id)
    
    if not activity:
        await query.edit_message_text("❌ Активность не найдена")
        return
    
    database.delete_activity(activity_id)
    await query.edit_message_text(f"✅ Активность '{activity['title']}' удалена!")
    
    # Возвращаемся в соответствующий список
    back_callback = "activities_planned" if activity['status'] == 'planned' else "activities_done"
    if back_callback == "activities_planned":
        await activities_planned_list(update, context)
    else:
        await activities_done_list(update, context)


async def activities_add_start(update: Update, context) -> None:
    """Начало добавления активности."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("➕ Добавление активности\n\nВведите название активности:")
    return ACTIVITY_TITLE


async def activities_add_title(update: Update, context) -> None:
    """Обработка названия активности."""
    title = update.message.text.strip()
    if not title:
        await update.message.reply_text("❌ Название не может быть пустым. Попробуйте еще раз:")
        return ACTIVITY_TITLE
    
    context.user_data['activity_title'] = title
    await update.message.reply_text("📝 Введите примечание (или /skip для пропуска):")
    return ACTIVITY_NOTE


async def activities_add_note(update: Update, context) -> None:
    """Обработка примечания активности."""
    note = update.message.text.strip() if update.message.text != "/skip" else None
    title = context.user_data['activity_title']
    
    activity_id = database.create_activity(title, note)
    
    await update.message.reply_text(f"✅ Активность '{title}' добавлена!")
    await activities_menu(update, context)
    return ConversationHandler.END


async def activities_add_cancel(update: Update, context) -> None:
    """Отмена добавления активности."""
    context.user_data.clear()
    await update.message.reply_text("❌ Добавление отменено")
    return ConversationHandler.END


def register_handlers(application: Application) -> None:
    """Регистрация обработчиков раздела активности."""
    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(activities_add_start, pattern="^activities_add$")],
        states={
            ACTIVITY_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, activities_add_title)],
            ACTIVITY_NOTE: [MessageHandler(filters.TEXT, activities_add_note)]
        },
        fallbacks=[CommandHandler("cancel", activities_add_cancel)]
    )
    
    application.add_handler(add_conv)
    application.add_handler(CallbackQueryHandler(activities_menu, pattern="^activities_menu$"))
    application.add_handler(CallbackQueryHandler(activities_planned_list, pattern="^activities_planned$"))
    application.add_handler(CallbackQueryHandler(activities_done_list, pattern="^activities_done$"))
    application.add_handler(CallbackQueryHandler(activity_detail, pattern="^activity_\\d+$"))
    application.add_handler(CallbackQueryHandler(activity_done, pattern="^activity_done_\\d+$"))
    application.add_handler(CallbackQueryHandler(activity_delete, pattern="^activity_delete_\\d+$"))

