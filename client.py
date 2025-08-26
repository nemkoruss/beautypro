from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import logging
from config import Config
from database import Database

logger = logging.getLogger(__name__)

# States
SELECTING_CATEGORY, SELECTING_SERVICE, GETTING_PHONE, GETTING_NAME = range(4)

db = Database()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Check if user is admin
    if user_id in Config.ADMIN_IDS:
        await update.message.reply_text(
            "Добро пожаловать в панель администратора!",
            reply_markup=ReplyKeyboardMarkup([['/admin']], resize_keyboard=True)
        )
        return

    # Regular user flow
    categories = db.get_all_categories()
    keyboard = [[category] for category in categories]
    keyboard.append(['Перейти в телеграм-канал', 'Перейти на сайт'])
    keyboard.append(['Адрес студии'])

    await update.message.reply_text(
        'Рады Вас видеть в нашей студии маникюра "Ноготочки-Точка"!',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text
    services = db.get_services_by_category(category)

    if not services:
        await update.message.reply_text("Категория не найдена.")
        return

    keyboard = [[f"{service[1]} - {service[2]} руб."] for service in services]
    keyboard.append(['Назад'])

    context.user_data['selected_category'] = category
    await update.message.reply_text(
        f"Выберите услугу в категории '{category}':",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service_name = update.message.text.split(' - ')[0]
    category = context.user_data.get('selected_category')

    services = db.get_services_by_category(category)
    selected_service = None

    for service in services:
        if service[1] == service_name:
            selected_service = service
            break

    if not selected_service:
        await update.message.reply_text("Услуга не найдена.")
        return

    context.user_data['selected_service'] = {
        'id': selected_service[0],
        'name': selected_service[1],
        'price': selected_service[2],
        'duration': selected_service[3]
    }

    await update.message.reply_text(
        f"Вы выбрали: {selected_service[1]}\n"
        f"Цена: {selected_service[2]} руб.\n"
        f"Время: {selected_service[3]}\n\n"
        "Введите ваш номер телефона:",
        reply_markup=ReplyKeyboardRemove()
    )

    return GETTING_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    context.user_data['phone'] = phone

    await update.message.reply_text("Теперь введите ваше имя:")
    return GETTING_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    phone = context.user_data['phone']
    service = context.user_data['selected_service']
    category = context.user_data['selected_category']

    # Save client to database
    client_id = db.add_client(
        update.effective_user.id,
        name,
        phone,
        category,
        service['name'],
        service['price'],
        service['duration']
    )

    if client_id:
        # Notify admin
        for admin_id in Config.ADMIN_IDS:
            try:
                await context.bot.send_message(
                    admin_id,
                    f"🔥 Новая запись! 🔥\n"
                    f"Клиент № {client_id}:\n"
                    f"Имя - {name}\n"
                    f"Телефон - {phone}\n"
                    f"Категория услуг - {category}\n"
                    f"Услуга - {service['name']}\n"
                    f"Стоимость - {service['price']} руб.\n"
                    f"Время оказания услуги - {service['duration']}\n\n"
                    "Свяжитесь с клиентом для согласования дня и времени для оказания услуг!"
                )
            except Exception as e:
                logger.error(f"Error sending notification to admin {admin_id}: {e}")

        await update.message.reply_text(
            "✅ Ваша запись принята! Администратор свяжется с вами для уточнения времени.\n\n"
            "Чем ещё можем помочь?",
            reply_markup=ReplyKeyboardMarkup([['/start']], resize_keyboard=True)
        )
    else:
        await update.message.reply_text(
            "❌ Произошла ошибка при записи. Пожалуйста, попробуйте позже."
        )

    return ConversationHandler.END

async def handle_contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == 'Перейти в телеграм-канал' and Config.TELEGRAM_CHANNEL:
        await update.message.reply_text(f"Наш телеграм-канал: {Config.TELEGRAM_CHANNEL}")

    elif text == 'Перейти на сайт' and Config.WEBSITE_URL:
        await update.message.reply_text(f"Наш сайт: {Config.WEBSITE_URL}")

    elif text == 'Адрес студии':
        if Config.LOCATION_COORDINATES:
            lat, lon = map(float, Config.LOCATION_COORDINATES)
            await update.message.reply_location(latitude=lat, longitude=lon)
        else:
            await update.message.reply_text("Адрес студии: ул. Примерная, д. 123")

    elif text == 'Назад':
        categories = db.get_all_categories()
        keyboard = [[category] for category in categories]
        keyboard.append(['Перейти в телеграм-канал', 'Перейти на сайт'])
        keyboard.append(['Адрес студии'])

        await update.message.reply_text(
            "Выберите категорию услуг:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=ReplyKeyboardMarkup([['/start']], resize_keyboard=True)
    )
    return ConversationHandler.END
