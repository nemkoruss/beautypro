import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from config import Config
from client import ClientHandler, PHONE, NAME
from admin import AdminHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

class BeautyBot:
    def __init__(self):
        self.client_handler = ClientHandler()
        self.admin_handler = AdminHandler()

        try:
            self.application = Application.builder().token(Config.BOT_TOKEN).build()
            logger.info("Приложение бота создано успешно")
        except Exception as e:
            logger.error(f"Ошибка создания приложения: {e}")
            raise

    def setup_handlers(self):
        try:
            # Обработчик команды /start
            self.application.add_handler(CommandHandler("start", self.client_handler.start))

            # Обработчик команды /admin
            self.application.add_handler(CommandHandler("admin", self.admin_handler.admin_panel))

            # ConversationHandler для записи на прием
            appointment_conv = ConversationHandler(
                entry_points=[MessageHandler(filters.Regex(r'.+ - \d+ руб\. .+'), self.client_handler.start_appointment)],
                states={
                    PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.client_handler.get_phone)],
                    NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.client_handler.get_name)],
                },
                fallbacks=[CommandHandler("cancel", self.client_handler.cancel)]
            )
            self.application.add_handler(appointment_conv)

            # Обработчики основных кнопок
            self.application.add_handler(MessageHandler(filters.Regex(r'^(Маникюр|Педикюр|Наращивание)$'),
                                                      self.client_handler.show_services))

            self.application.add_handler(MessageHandler(filters.Regex(r'^Перейти в телеграм-канал$'),
                                                      self.client_handler.show_telegram_channel))

            self.application.add_handler(MessageHandler(filters.Regex(r'^Перейти на сайт$'),
                                                      self.client_handler.show_website))

            self.application.add_handler(MessageHandler(filters.Regex(r'^Адрес студии$'),
                                                      self.client_handler.show_address))

            self.application.add_handler(MessageHandler(filters.Regex(r'^Назад$'),
                                                      self.client_handler.back_to_start))

            # Административные обработчики
            self.application.add_handler(MessageHandler(filters.Regex(r'^Список клиентов$'),
                                                      self.admin_handler.show_clients))

            self.application.add_handler(MessageHandler(filters.Regex(r'^Записи за 30 дней$'),
                                                      self.admin_handler.show_appointments))

            self.application.add_handler(MessageHandler(filters.Regex(r'^В главное меню$'),
                                                      self.client_handler.start))

            # Обработчик для любых других сообщений
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.client_handler.handle_unknown))

            logger.info("Все обработчики установлены")

        except Exception as e:
            logger.error(f"Ошибка установки обработчиков: {e}")
            raise

    def run(self):
        try:
            self.setup_handlers()
            logger.info("Бот запускается...")
            print("Бот запущен! Для остановки нажмите Ctrl+C")
            self.application.run_polling()
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            raise

if __name__ == "__main__":
    try:
        # Проверяем конфигурацию
        config_status = Config.check_config()
        print("Статус конфигурации:", config_status)

        if not all(config_status.values()):
            print("ВНИМАНИЕ: Не все переменные окружения загружены!")
            print("Проверьте файл .env")

        bot = BeautyBot()
        bot.run()

    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        print(f"Ошибка: {e}")
