from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import logging
from config import Config
from database import Database

logger = logging.getLogger(__name__)

# Admin states
ADMIN_MAIN, SELECT_CATEGORY, SELECT_SERVICE, EDIT_SERVICE, ADD_SERVICE_CATEGORY, ADD_SERVICE_NAME, ADD_SERVICE_PRICE, ADD_SERVICE_DURATION = range(8)

db = Database()

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in Config.ADMIN_IDS:
        await update.message.reply_text("Доступ запрещен.")
        return

    keyboard = [
        ['Изменить услугу', 'Удалить услугу'],
        ['Добавить услугу', 'Информационное сообщение'],
        ['Посмотреть список клиентов', 'Посмотреть записи'],
        ['Выйти из админки']
    ]

    await update.message.reply_text(
        "Панель администратора:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return ADMIN_MAIN

async def handle_admin_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text

    if choice == 'Изменить услугу':
        categories = db.get_all_categories()
        keyboard = [[category] for category in categories]
        keyboard.append(['Назад'])

        await update.message.reply_text(
            "Выберите категорию для изменения:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return SELECT_CATEGORY

    elif choice == 'Удалить услугу':
        categories = db.get_all_categories()
        keyboard = [[category] for category in categories]
        keyboard.append(['Назад'])

        await update.message.reply_text(
            "Выберите категорию для удаления:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return SELECT_CATEGORY

    elif choice == 'Добавить услугу':
        categories = db.get_all_categories()
        keyboard = [[category] for category in categories]
        keyboard.append(['Назад'])

        await update.message.reply_text(
            "Выберите категорию для добавления услуги:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return ADD_SERVICE_CATEGORY

    elif choice == 'Информационное сообщение':
        await update.message.reply_text(
            "Введите сообщение для рассылки:",
            reply_markup=ReplyKeyboardMarkup([['Отмена']], resize_keyboard=True)
        )
        # This would need additional implementation for broadcasting

    elif choice == 'Посмотреть список клиентов':
        clients = db.get_all_clients()
        if clients:
            message = "📋 Список всех клиентов:\n\n"
            for client in clients:
                message += f"ID: {client[0]}\nИмя: {client[1]}\nТелефон: {client[2]}\nУслуга: {client[4]} ({client[3]})\nЦена: {client[5]} руб.\nДата: {client[7]}\nСтатус: {client[8]}\n\n"
            await update.message.reply_text(message[:4000])
        else:
            await update.message.reply_text("Клиентов пока нет.")

    elif choice == 'Посмотреть записи':
        clients = db.get_recent_clients(30)
        if clients:
            message = "📅 Записи за последние 30 дней:\n\n"
            for client in clients:
                message += f"ID: {client[0]}\nИмя: {client[1]}\nТелефон: {client[2]}\nУслуга: {client[4]} ({client[3]})\nЦена: {client[5]} руб.\nДата: {client[7]}\nСтатус: {client[8]}\n\n"
            await update.message.reply_text(message[:4000])
        else:
            await update.message.reply_text("Записей за последние 30 дней нет.")

    elif choice == 'Выйти из админки':
        await update.message.reply_text(
            "Вы вышли из панели администратора.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text
    context.user_data['admin_category'] = category

    services = db.get_services_by_category(category)
    keyboard = [[service[1]] for service in services]
    keyboard.append(['Назад'])

    await update.message.reply_text(
        f"Выберите услугу в категории '{category}':",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return SELECT_SERVICE

async def handle_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service_name = update.message.text
    category = context.user_data['admin_category']

    services = db.get_services_by_category(category)
    selected_service = None

    for service in services:
        if service[1] == service_name:
            selected_service = service
            break

    if not selected_service:
        await update.message.reply_text("Услуга не найдена.")
        return ADMIN_MAIN

    context.user_data['admin_service'] = selected_service

    await update.message.reply_text(
        f"Услуга: {selected_service[1]}\n"
        f"Цена: {selected_service[2]} руб.\n"
        f"Время: {selected_service[3]}\n\n"
        "Введите новое название услуги:",
        reply_markup=ReplyKeyboardRemove()
    )
    return EDIT_SERVICE

async def edit_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text
    context.user_data['new_service_name'] = new_name

    await update.message.reply_text("Введите новую цену услуги:")
    return EDIT_SERVICE

async def add_service_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text
    context.user_data['new_service_category'] = category

    await update.message.reply_text("Введите название новой услуги:")
    return ADD_SERVICE_NAME

async def add_service_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    context.user_data['new_service_name'] = name

    await update.message.reply_text("Введите цену услуги:")
    return ADD_SERVICE_PRICE

async def add_service_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text)
        context.user_data['new_service_price'] = price

        await update.message.reply_text("Введите время оказания услуги (например, '2 часа'):")
        return ADD_SERVICE_DURATION
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректную цену (число):")
        return ADD_SERVICE_PRICE

async def add_service_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    duration = update.message.text
    category = context.user_data['new_service_category']
    name = context.user_data['new_service_name']
    price = context.user_data['new_service_price']

    if db.add_service(category, name, price, duration):
        await update.message.reply_text("✅ Услуга успешно добавлена!")
    else:
        await update.message.reply_text("❌ Ошибка при добавлении услуги.")

    return ConversationHandler.END

async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=ReplyKeyboardMarkup([['/admin']], resize_keyboard=True)
    )
    return ConversationHandler.END
