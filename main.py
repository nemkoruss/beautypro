import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from config import Config
from client import *
from admin import *

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    # Check if bot token is configured
    if not Config.BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables!")
        return

    # Create application
    application = Application.builder().token(Config.BOT_TOKEN).build()

    # Client conversation handler
    client_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_selection)
            ],
            SELECTING_SERVICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_service_selection)
            ],
            GETTING_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)
            ],
            GETTING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Admin conversation handler
    admin_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('admin', admin_panel)],
        states={
            ADMIN_MAIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_main)
            ],
            SELECT_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_selection)
            ],
            SELECT_SERVICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_service_selection)
            ],
            EDIT_SERVICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_service)
            ],
            ADD_SERVICE_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_service_category)
            ],
            ADD_SERVICE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_service_name)
            ],
            ADD_SERVICE_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_service_price)
            ],
            ADD_SERVICE_DURATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_service_duration)
            ]
        },
        fallbacks=[CommandHandler('cancel', admin_cancel)]
    )

    # Add handlers
    application.add_handler(client_conv_handler)
    application.add_handler(admin_conv_handler)

    # Handle contact information buttons
    application.add_handler(MessageHandler(
        filters.Text(['Перейти в телеграм-канал', 'Перейти на сайт', 'Адрес студии', 'Назад']),
        handle_contact_info
    ))

    # Start the bot
    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
