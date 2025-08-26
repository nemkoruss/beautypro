from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import logging
from config import Config
from database import Database

logger = logging.getLogger(__name__)

class AdminHandler:
    def __init__(self):
        self.db = Database()

    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in Config.ADMIN_IDS:
            await update.message.reply_text("У вас нет доступа к панели администратора.")
            return

        keyboard = [
            ['Список клиентов', 'Записи за 30 дней'],
            ['В главное меню']
        ]

        await update.message.reply_text(
            "Панель администратора:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    async def show_clients(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in Config.ADMIN_IDS:
            await update.message.reply_text("У вас нет доступа к этой функции.")
            return

        clients = self.db.get_clients()

        if not clients:
            await update.message.reply_text("Клиентов пока нет.")
            return

        response = "📋 Список клиентов:\n\n"
        for client in clients:
            response += f"• ID: {client['id']}, Имя: {client['name']}, Телефон: {client['phone']}, Дата: {client['created_at']}\n"

        # Разбиваем на части из-за ограничения длины сообщения в Telegram
        for i in range(0, len(response), 4000):
            await update.message.reply_text(response[i:i+4000])

    async def show_appointments(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in Config.ADMIN_IDS:
            await update.message.reply_text("У вас нет доступа к этой функции.")
            return

        appointments = self.db.get_appointments_last_30_days()

        if not appointments:
            await update.message.reply_text("Записей за последние 30 дней нет.")
            return

        response = "📅 Записи за последние 30 дней:\n\n"
        for app in appointments:
            response += f"• Клиент: {app['name']}, Тел: {app['phone']}, Услуга: {app['service_name']}, Цена: {app['price']} руб., Дата: {app['created_at']}\n"

        # Разбиваем на части
        for i in range(0, len(response), 4000):
            await update.message.reply_text(response[i:i+4000])

    async def back_to_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.admin_panel(update, context)
