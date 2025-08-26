from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import logging
from config import config
from database import db

# Состояния для ConversationHandler
PHONE, NAME = range(2)

# Настройка логирования
logging.basicConfig(
    filename='bot.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id

    # Проверяем, является ли пользователь администратором
    if user_id in config.ADMIN_IDS:
        # Для администраторов показываем админ-меню
        from admin import show_admin_menu
        return await show_admin_menu(update, context)

    # Для обычных пользователей показываем клиентское меню
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ главного меню"""
    keyboard = [
        ['Маникюр', 'Педикюр'],
        ['Наращивание', 'Адрес студии'],
        ['Перейти в телеграм-канал', 'Перейти на сайт']
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    welcome_text = (
        "Рады Вас видеть в нашей студии маникюра \"Ноготочки-Точка\"! 🎉\n\n"
        "Выберите интересующую вас услугу:"
    )

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    else:
        await update.callback_query.message.reply_text(welcome_text, reply_markup=reply_markup)

async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора категории"""
    category = update.message.text
    services = db.get_services_by_category(category)

    if not services:
        await update.message.reply_text("В этой категории пока нет услуг.")
        return

    keyboard = []
    for service in services:
        service_text = f"{service['name']} - {service['price']} руб., {service['duration']}"
        keyboard.append([service_text])

    keyboard.append(['Назад'])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"Услуги {category}:", reply_markup=reply_markup)

    # Сохраняем выбранную категорию в контексте
    context.user_data['category'] = category

async def handle_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора услуги"""
    service_text = update.message.text

    if service_text == 'Назад':
        await show_main_menu(update, context)
        return

    # Ищем услугу в базе данных
    services = db.get_services_by_category(context.user_data.get('category', ''))
    selected_service = None

    for service in services:
        service_display = f"{service['name']} - {service['price']} руб., {service['duration']}"
        if service_display == service_text:
            selected_service = service
            break

    if not selected_service:
        await update.message.reply_text("Услуга не найдена.")
        return

    # Сохраняем выбранную услугу
    context.user_data['selected_service'] = selected_service

    # Запрашиваем номер телефона
    phone_keyboard = [[KeyboardButton("Отправить номер телефона", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(phone_keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Отлично! Для записи нам нужен ваш номер телефона. "
        "Нажмите кнопку ниже или введите номер вручную:",
        reply_markup=reply_markup
    )

    return PHONE

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка номера телефона"""
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text

    # Проверяем формат номера
    if not phone.replace('+', '').replace(' ', '').replace('-', '').isdigit():
        await update.message.reply_text("Пожалуйста, введите корректный номер телефона:")
        return PHONE

    context.user_data['phone'] = phone

    # Запрашиваем имя
    await update.message.reply_text(
        "Отлично! Теперь введите ваше имя:",
        reply_markup=ReplyKeyboardRemove()
    )

    return NAME

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка имени и завершение записи"""
    name = update.message.text
    service = context.user_data.get('selected_service')
    phone = context.user_data.get('phone')
    user_id = update.effective_user.id

    if not all([service, phone, name]):
        await update.message.reply_text("Произошла ошибка. Пожалуйста, начните заново.")
        return ConversationHandler.END

    # Сохраняем клиента в базу данных
    client_id = db.add_client(user_id, name, phone, service['id'])

    if client_id:
        # Отправляем сообщение администраторам
        admin_message = (
            f"🎉 Новая запись! Клиент №{client_id}:\n"
            f"👤 Имя: {name}\n"
            f"📞 Телефон: {phone}\n"
            f"📋 Категория: {service['category']}\n"
            f"💅 Услуга: {service['name']}\n"
            f"💰 Стоимость: {service['price']} руб.\n"
            f"⏰ Время: {service['duration']}\n\n"
            f"Свяжитесь с клиентом для согласования дня и времени!"
        )

        for admin_id in config.ADMIN_IDS:
            try:
                await context.bot.send_message(admin_id, admin_message)
            except Exception as e:
                logging.error(f"Ошибка отправки сообщения администратору {admin_id}: {e}")

        # Сообщение клиенту
        await update.message.reply_text(
            "✅ Спасибо за запись! Мы свяжемся с вами в ближайшее время "
            "для согласования даты и времени визита.",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
            "Произошла ошибка при записи. Пожалуйста, попробуйте позже."
        )

    await show_main_menu(update, context)
    return ConversationHandler.END

async def handle_contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка контактной информации"""
    text = update.message.text

    if text == 'Адрес студии':
        if config.LOCATION_COORDINATES:
            try:
                lat, lon = map(float, config.LOCATION_COORDINATES.split(','))
                await update.message.reply_location(latitude=lat, longitude=lon)
                await update.message.reply_text("📍 Наш адрес на карте:")
            except:
                await update.message.reply_text("Адрес временно недоступен.")
        else:
            await update.message.reply_text("Информация об адресе временно недоступна.")

    elif text == 'Перейти в телеграм-канал':
        if config.TELEGRAM_CHANNEL:
            await update.message.reply_text(f"Присоединяйтесь к нашему каналу: {config.TELEGRAM_CHANNEL}")
        else:
            await update.message.reply_text("Ссылка на канал временно недоступна.")

    elif text == 'Перейти на сайт':
        if config.WEBSITE_URL:
            await update.message.reply_text(f"Посетите наш сайт: {config.WEBSITE_URL}")
        else:
            await update.message.reply_text("Ссылка на сайт временно недоступна.")

    elif text == 'Позвонить':
        if config.PHONE_NUMBER:
            await update.message.reply_text(f"Наш телефон: {config.PHONE_NUMBER}")
        else:
            await update.message.reply_text("Номер телефона временно недоступен.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена текущей операции"""
    await update.message.reply_text(
        "Операция отменена.",
        reply_markup=ReplyKeyboardRemove()
    )
    await show_main_menu(update, context)
    return ConversationHandler.END

# Создаем ConversationHandler для записи
conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex(r'.* - \d+ руб., .*'), handle_service_selection)],
    states={
        PHONE: [MessageHandler(filters.CONTACT | filters.TEXT & ~filters.COMMAND, handle_phone)],
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
    },
    fallbacks=[MessageHandler(filters.Regex('^Отмена$'), cancel)]
)
