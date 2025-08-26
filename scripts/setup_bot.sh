#!/bin/bash

# Скрипт установки для телеграм бота студии маникюра

echo "🐾 Начинаем установку бота для студии маникюра..."

# Обновление системы
echo "🔄 Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Проверка и установка необходимых пакетов
echo "🔍 Проверка установленных пакетов..."

# Проверка Git
if ! command -v git &> /dev/null; then
    echo "📦 Установка Git..."
    sudo apt install git -y
fi

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "🐍 Установка Python3..."
    sudo apt install python3 -y
fi

# Проверка pip
if ! command -v pip3 &> /dev/null; then
    echo "📦 Установка pip3..."
    sudo apt install python3-pip -y
fi

# Создание директории для проекта
PROJECT_DIR="beautypro"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "📁 Создание директории проекта..."
    mkdir $PROJECT_DIR
fi

cd $PROJECT_DIR

# Установка зависимостей
echo "📦 Установка зависимостей из requirements.txt..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
else
    echo "❌ Файл requirements.txt не найден!"
    exit 1
fi

# Создание .env файла
echo "⚙️ Создание файла конфигурации .env..."

cat > .env << EOF
# Токен вашего телеграм бота
BOT_TOKEN=your_bot_token_here

# ID администраторов (через запятую)
ADMIN_IDS=123456789,987654321

# Контактная информация
PHONE_NUMBER=+79991234567
WEBSITE_URL=https://ваш-сайт.ru
TELEGRAM_CHANNEL=https://t.me/ваш_канал
LOCATION_COORDINATES=55.7558,37.6173
EOF

echo "📝 Файл .env создан. Пожалуйста, отредактируйте его и добавьте реальные значения."

# Создание базы данных
echo "🗄️ Инициализация базы данных..."
python3 -c "
from database import db
print('✅ База данных создана успешно!')
"

echo "🎉 Установка завершена!"
echo "📋 Далее:"
echo "1. Отредактируйте файл .env с реальными значениями"
echo "2. Запустите бота командой: python3 main.py"
echo "3. Бот готов к работе!"

# Даем права на выполнение скрипта
chmod +x $0
