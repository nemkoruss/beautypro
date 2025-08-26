from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
import logging
from config import config
from client import conv_handler, start, handle_category, handle_contact_info
from admin import admin_command, admin_conv_handler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)

logger = logging.getLogger(__name__)

def main():
    """Основная функция запуска бота"""
    # Проверка конфигурации
    config_status = config.check_config()
    missing_configs = [key for key, value in config_status.items() if not value]

    if missing_configs:
        logger.error(f"Отсутствуют конфигурационные параметры: {', '.join(missing_configs)}")
        print(f"Ошибка: отсутствуют конфигурационные параметры: {', '.join(missing_configs)}")
        return

    if not config.BOT_TOKEN:
        logger.error("Токен бота не установлен!")
        print("Ошибка: токен бота не установлен!")
        return

    # Создание приложения
    application = Application.builder().token(config.BOT_TOKEN).build()

    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(conv_handler)
    application.add_handler(admin_conv_handler)

    # Обработчики категорий
    application.add_handler(MessageHandler(filters.Regex('^(Маникюр|Педикюр|Наращивание)$'), handle_category))

    # Обработчики контактной информации
    application.add_handler(MessageHandler(
        filters.Regex('^(Адрес студии|Перейти в телеграм-канал|Перейти на сайт|Позвонить)$'),
        handle_contact_info
    ))

    # Обработчик неизвестных команд
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown))

    # Запуск бота
    print("Бот запущен...")
    application.run_polling()

async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик неизвестных команд"""
    await update.message.reply_text("Извините, я не понимаю эту команду. Используйте /start для начала.")

if __name__ == '__main__':
    main()
