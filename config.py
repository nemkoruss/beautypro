import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

class Config:
    # Токен бота
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')

    # ID администраторов (разделенные запятыми)
    ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]

    # Контактная информация
    PHONE_NUMBER = os.getenv('PHONE_NUMBER', '')
    WEBSITE_URL = os.getenv('WEBSITE_URL', '')
    TELEGRAM_CHANNEL = os.getenv('TELEGRAM_CHANNEL', '')
    LOCATION_COORDINATES = os.getenv('LOCATION_COORDINATES', '')

    # Настройки базы данных
    DATABASE_NAME = 'beauty_salon.db'

    # Проверка загрузки переменных
    def check_config(self):
        config_status = {
            'BOT_TOKEN': bool(self.BOT_TOKEN),
            'ADMIN_IDS': bool(self.ADMIN_IDS),
            'PHONE_NUMBER': bool(self.PHONE_NUMBER),
            'WEBSITE_URL': bool(self.WEBSITE_URL),
            'TELEGRAM_CHANNEL': bool(self.TELEGRAM_CHANNEL),
            'LOCATION_COORDINATES': bool(self.LOCATION_COORDINATES)
        }
        return config_status

# Создаем экземпляр конфигурации
config = Config()
