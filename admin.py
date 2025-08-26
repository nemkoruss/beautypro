from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import logging
from config import config
from database import db

# Состояния для админских ConversationHandler
ADMIN_ACTION, EDIT_SERVICE, DELETE_SERVICE, ADD_SERVICE, BROADCAST_MESSAGE = range(5)

# Настройка логирования
logging.basicConfig(
    filename='bot.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /admin"""
    user_id = update.effective_user.id

    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("У вас нет прав доступа к админ-панели.")
        return

    await show_admin_menu(update, context)

async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ админского меню"""
    keyboard = [
        ['Изменить услугу', 'Удалить услугу'],
        ['Добавить услугу', 'Информационное сообщение'],
        ['Посмотреть список клиентов', 'Посмотреть записи'],
        ['В главное меню']
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    if update.message:
        await update.message.reply_text("Админ-панель:", reply_markup=reply_markup)
    else:
        await update.callback_query.message.reply_text("Админ-панель:", reply_markup=reply_markup)

    return ADMIN_ACTION

async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка действий в админ-панели"""
    action = update.message.text

    if action == 'В главное меню':
        from client import show_main_menu
        await show_main_menu(update, context)
        return ConversationHandler.END

    elif action == 'Изменить услугу':
        await show_categories_for_edit(update, context)
        return EDIT_SERVICE

    elif action == 'Удалить услугу':
        await show_categories_for_delete(update, context)
        return DELETE_SERVICE

    elif action == 'Добавить услугу':
        await show_categories_for_add(update, context)
        return ADD_SERVICE

    elif action == 'Информационное сообщение':
        await update.message.reply_text(
            "Введите сообщение для рассылки всем клиентам:",
            reply_markup=ReplyKeyboardMarkup([['Отмена']], resize_keyboard=True)
        )
        return BROADCAST_MESSAGE

    elif action == 'Посмотреть список клиентов':
        clients = db.get_all_clients()
        await send_clients_list(update, clients, "Все клиенты:")

    elif action == 'Посмотреть записи':
        clients = db.get_recent_clients(30)
        await send_clients_list(update, clients, "Записи за последние 30 дней:")

async def show_categories_for_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ категорий для редактирования"""
    keyboard = [['Маникюр', 'Педикюр'], ['Наращивание', 'Назад']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите категорию для редактирования:", reply_markup=reply_markup)

async def show_services_for_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ услуг для редактирования"""
    category = update.message.text

    if category == 'Назад':
        await show_admin_menu(update, context)
        return ADMIN_ACTION

    services = db.get_services_by_category(category)

    if not services:
        await update.message.reply_text("В этой категории нет услуг.")
        return EDIT_SERVICE

    keyboard = []
    for service in services:
        keyboard.append([f"{service['name']} (ID: {service['id']})"])
    keyboard.append(['Назад'])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"Услуги {category}:", reply_markup=reply_markup)

    context.user_data['edit_category'] = category
    return EDIT_SERVICE

async def handle_service_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка редактирования услуги"""
    service_text = update.message.text

    if service_text == 'Назад':
        await show_categories_for_edit(update, context)
        return EDIT_SERVICE

    # Извлекаем ID услуги
    try:
        service_id = int(service_text.split('(ID: ')[1].split(')')[0])
    except:
        await update.message.reply_text("Неверный формат услуги.")
        return EDIT_SERVICE

    service = db.get_service_by_id(service_id)
    if not service:
        await update.message.reply_text("Услуга не найдена.")
        return EDIT_SERVICE

    context.user_data['edit_service_id'] = service_id
    context.user_data['edit_service'] = service

    await update.message.reply_text(
        f"Редактирование услуги: {service['name']}\n\n"
        f"Текущие данные:\n"
        f"Название: {service['name']}\n"
        f"Цена: {service['price']} руб.\n"
        f"Время: {service['duration']}\n\n"
        "Введите новое название услуги:",
        reply_markup=ReplyKeyboardRemove()
    )

    return EDIT_SERVICE

async def handle_service_name_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нового названия услуги"""
    new_name = update.message.text
    context.user_data['new_service_name'] = new_name

    await update.message.reply_text("Введите новую цену услуги (только цифры):")
    return EDIT_SERVICE

async def handle_service_price_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка новой цены услуги"""
    try:
        new_price = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректную цену (только цифры):")
        return EDIT_SERVICE

    context.user_data['new_service_price'] = new_price

    await update.message.reply_text("Введите новое время оказания услуги (например: '2 часа'):")
    return EDIT_SERVICE

async def handle_service_duration_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нового времени услуги и сохранение"""
    new_duration = update.message.text
    service_id = context.user_data.get('edit_service_id')
    new_name = context.user_data.get('new_service_name')
    new_price = context.user_data.get('new_service_price')

    if not all([service_id, new_name, new_price, new_duration]):
        await update.message.reply_text("Произошла ошибка. Пожалуйста, начните заново.")
        return await show_admin_menu(update, context)

    # Обновляем услугу в базе данных
    success = db.update_service(service_id, new_name, new_price, new_duration)

    if success:
        await update.message.reply_text("✅ Услуга успешно обновлена!")
    else:
        await update.message.reply_text("❌ Ошибка при обновлении услуги.")

    await show_admin_menu(update, context)
    return ADMIN_ACTION

# Аналогичные функции для удаления и добавления услуг будут реализованы по аналогии

async def send_clients_list(update: Update, clients, title):
    """Отправка списка клиентов"""
    if not clients:
        await update.message.reply_text("Клиентов не найдено.")
        return

    message = f"{title}\n\n"
    for i, client in enumerate(clients, 1):
        message += (
            f"{i}. {client['name']} - {client['phone']}\n"
            f"   Услуга: {client.get('service_name', 'Не указана')}\n"
            f"   Дата: {client['appointment_date']}\n"
            f"   Статус: {client['status']}\n\n"
        )

    # Разбиваем сообщение на части, если оно слишком длинное
    if len(message) > 4096:
        for i in range(0, len(message), 4096):
            await update.message.reply_text(message[i:i+4096])
    else:
        await update.message.reply_text(message)

async def cancel_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена админской операции"""
    await update.message.reply_text(
        "Операция отменена.",
        reply_markup=ReplyKeyboardRemove()
    )
    await show_admin_menu(update, context)
    return ConversationHandler.END

# ConversationHandler для админских операций
admin_conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex('^(Изменить услугу|Удалить услугу|Добавить услугу|Информационное сообщение)$'), handle_admin_action)],
    states={
        ADMIN_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_action)],
        EDIT_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_service_edit)],
        # Добавить остальные состояния...
    },
    fallbacks=[MessageHandler(filters.Regex('^Отмена$'), cancel_admin)]
)
