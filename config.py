import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot token
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')

    # Admin IDs (comma separated)
    ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]

    # Contact information
    PHONE_NUMBER = os.getenv('PHONE_NUMBER', '')
    WEBSITE_URL = os.getenv('WEBSITE_URL', '')
    TELEGRAM_CHANNEL = os.getenv('TELEGRAM_CHANNEL', '')
    LOCATION_COORDINATES = os.getenv('LOCATION_COORDINATES', '').split(',') if os.getenv('LOCATION_COORDINATES') else None

    # Database
    DATABASE_NAME = 'beauty_salon.db'

    # Debug information
    DEBUG = {
        'BOT_TOKEN': bool(BOT_TOKEN),
        'ADMIN_IDS': bool(ADMIN_IDS),
        'PHONE_NUMBER': bool(PHONE_NUMBER),
        'WEBSITE_URL': bool(WEBSITE_URL),
        'TELEGRAM_CHANNEL': bool(TELEGRAM_CHANNEL),
        'LOCATION_COORDINATES': bool(LOCATION_COORDINATES)
    }

# Print debug information
if __name__ == '__main__':
    print("Configuration status:")
    for key, value in Config.DEBUG.items():
        status = "✓ LOADED" if value else "✗ MISSING"
        print(f"{key}: {status}")
