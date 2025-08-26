import os
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')

    ADMIN_IDS = []
    admin_ids_str = os.getenv('ADMIN_IDS', '')
    if admin_ids_str:
        try:
            ADMIN_IDS = [int(admin_id.strip()) for admin_id in admin_ids_str.split(',')]
        except ValueError:
            logger.error("Ошибка в формате ADMIN_IDS")

    PHONE_NUMBER = os.getenv('PHONE_NUMBER', '')
    WEBSITE_URL = os.getenv('WEBSITE_URL', '')
    TELEGRAM_CHANNEL = os.getenv('TELEGRAM_CHANNEL', '')
    MAP_COORDINATES = os.getenv('MAP_COORDINATES', '')

    # Проверка загрузки переменных
    @classmethod
    def check_config(cls):
        config_status = {
            'BOT_TOKEN': bool(cls.BOT_TOKEN),
            'ADMIN_IDS': bool(cls.ADMIN_IDS),
            'PHONE_NUMBER': bool(cls.PHONE_NUMBER),
            'WEBSITE_URL': bool(cls.WEBSITE_URL),
            'TELEGRAM_CHANNEL': bool(cls.TELEGRAM_CHANNEL),
            'MAP_COORDINATES': bool(cls.MAP_COORDINATES)
        }
        return config_status

# Для отладки
if __name__ == "__main__":
    print("Config status:", Config.check_config())
