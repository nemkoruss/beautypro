from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import logging
import re
from config import Config
from database import Database

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
PHONE, NAME = range(2)

class ClientHandler:
    def __init__(self):
        self.db = Database()
        self.user_states = {}  # Для отслеживания состояний пользователей

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id

            # Проверяем, является ли пользователь администратором
            if user_id in Config.ADMIN_IDS:
                await update.message.reply_text(
                    "Добро пожаловать в панель администратора!",
                    reply_markup=ReplyKeyboardMarkup([['/admin']], resize_keyboard=True)
                )
                return

            # Обычный пользователь
            welcome_text = "Рады Вас видеть в нашей студии маникюра \"Ноготочки-Точка\"!"
            keyboard = [
                ['Маникюр', 'Педикюр', 'Наращивание'],
                ['Перейти в телеграм-канал', 'Перейти на сайт'],
                ['Адрес студии']
            ]

            await update.message.reply_text(
                welcome_text,
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )

        except Exception as e:
            logger.error(f"Ошибка в start: {e}")
            await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

    async def show_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            category_name = update.message.text
            categories = self.db.get_categories()

            # Находим ID категории по имени
            category_id = None
            for cat_id, cat_name in categories:
                if cat_name == category_name:
                    category_id = cat_id
                    break

            if not category_id:
                await update.message.reply_text("Категория не найдена.")
                return

            services = self.db.get_services_by_category(category_id)

            if not services:
                await update.message.reply_text("В этой категории пока нет услуг.")
                return

            keyboard = []
            service_map = {}  # Для хранения соответствия текста кнопки и ID услуги

            for service in services:
                service_id, name, price, duration = service
                button_text = f"{name} - {price} руб. ({duration})"
                keyboard.append([button_text])
                service_map[button_text] = service_id

            keyboard.append(['Назад'])

            # Сохраняем mapping для этого пользователя
            user_id = update.effective_user.id
            self.user_states[user_id] = {'service_map': service_map}

            text = f"Услуги в категории '{category_name}':\n\n"
            for service in services:
                service_id, name, price, duration = service
                text += f"• {name} - {price} руб., {duration}\n"

            await update.message.reply_text(
                text,
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )

        except Exception as e:
            logger.error(f"Ошибка в show_services: {e}")
            await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

    async def start_appointment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id
            button_text = update.message.text

            # Проверяем, есть ли mapping для этого пользователя
            if user_id not in self.user_states or 'service_map' not in self.user_states[user_id]:
                await update.message.reply_text("Пожалуйста, выберите услугу из меню.")
                return ConversationHandler.END

            service_map = self.user_states[user_id]['service_map']

            if button_text in service_map:
                service_id = service_map[button_text]
                context.user_data['service_id'] = service_id

                await update.message.reply_text(
                    "Для записи на прием введите ваш номер телефона:",
                    reply_markup=ReplyKeyboardRemove()
                )

                return PHONE
            else:
                await update.message.reply_text("Пожалуйста, выберите услугу из меню.")
                return ConversationHandler.END

        except Exception as e:
            logger.error(f"Ошибка в start_appointment: {e}")
            await update.message.reply_text("Произошла ошибка. Попробуйте позже.")
            return ConversationHandler.END

    async def get_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            phone = update.message.text
            context.user_data['phone'] = phone

            await update.message.reply_text("Теперь введите ваше имя:")

            return NAME

        except Exception as e:
            logger.error(f"Ошибка в get_phone: {e}")
            await update.message.reply_text("Произошла ошибка. Попробуйте позже.")
            return ConversationHandler.END

    async def get_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            name = update.message.text
            phone = context.user_data['phone']
            service_id = context.user_data['service_id']

            # Сохраняем клиента и запись
            client_id = self.db.add_client(name, phone)
            appointment_id = self.db.add_appointment(client_id, service_id)

            # Получаем информацию об услуге
            service_info = self.db.get_service(service_id)

            if service_info:
                service_name, price, duration, category_name = service_info[1], service_info[2], service_info[3], service_info[4]

                # Сообщение для клиента
                await update.message.reply_text(
                    f"✅ Спасибо за запись!\n\n"
                    f"Ваши данные:\n"
                    f"• Имя: {name}\n"
                    f"• Телефон: {phone}\n"
                    f"• Услуга: {service_name}\n"
                    f"• Стоимость: {price} руб.\n\n"
                    f"Мы свяжемся с вами в ближайшее время для подтверждения.",
                    reply_markup=ReplyKeyboardMarkup([['/start']], resize_keyboard=True)
                )

                # Логируем для администратора
                admin_message = (
                    f"🎉 Новая запись! 🎉\n"
                    f"Клиент № {client_id}:\n"
                    f"Имя - {name}\n"
                    f"Телефон - {phone}\n"
                    f"Категория услуг - {category_name}\n"
                    f"Услуга - {service_name}\n"
                    f"Стоимость - {price} руб.\n"
                    f"Время оказания услуги - {duration}\n\n"
                    f"Свяжитесь с клиентом для согласования дня и времени!"
                )
                logger.info(admin_message)

            # Очищаем состояние пользователя
            user_id = update.effective_user.id
            if user_id in self.user_states:
                del self.user_states[user_id]

            return ConversationHandler.END

        except Exception as e:
            logger.error(f"Ошибка в get_name: {e}")
            await update.message.reply_text("Произошла ошибка при записи. Попробуйте позже.")
            return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Очищаем состояние пользователя
        user_id = update.effective_user.id
        if user_id in self.user_states:
            del self.user_states[user_id]

        await update.message.reply_text(
            "Запись отменена.",
            reply_markup=ReplyKeyboardMarkup([['/start']], resize_keyboard=True)
        )
        return ConversationHandler.END

    async def show_telegram_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"📢 Наш телеграм-канал: {Config.TELEGRAM_CHANNEL}")

    async def show_website(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"🌐 Наш сайт: {Config.WEBSITE_URL}")

    async def show_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"📍 Наш адрес: {Config.MAP_COORDINATES}")

    async def back_to_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Очищаем состояние пользователя
        user_id = update.effective_user.id
        if user_id in self.user_states:
            del self.user_states[user_id]

        await self.start(update, context)

    async def handle_unknown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик для неизвестных сообщений"""
        await update.message.reply_text(
            "Пожалуйста, используйте кнопки меню для навигации.",
            reply_markup=ReplyKeyboardMarkup([['/start']], resize_keyboard=True)
        )
