#!/bin/bash

# Обновление системы
echo "Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Проверка и установка необходимых пакетов
echo "Проверка установленных пакетов..."

# Проверка Git
if ! command -v git &> /dev/null; then
    echo "Установка Git..."
    sudo apt install git -y
else
    echo "Git уже установлен"
fi

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "Установка Python3..."
    sudo apt install python3 -y
else
    echo "Python3 уже установлен"
fi

# Проверка pip
if ! command -v pip3 &> /dev/null; then
    echo "Установка pip3..."
    sudo apt install python3-pip -y
else
    echo "pip3 уже установлен"
fi

# Установка зависимостей
echo "Установка зависимостей из requirements.txt..."
pip3 install -r requirements.txt

# Создание .env файла
echo "Создание .env файла..."
read -p "Введите BOT_TOKEN: " BOT_TOKEN
read -p "Введите ADMIN_IDS (через запятую): " ADMIN_IDS
read -p "Введите номер телефона: " PHONE_NUMBER
read -p "Введите ссылку на сайт: " WEBSITE_URL
read -p "Введите ссылку на телеграм-канал: " TELEGRAM_CHANNEL
read -p "Введите координаты: " MAP_COORDINATES

cat > .env << EOL
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=$ADMIN_IDS
PHONE_NUMBER=$PHONE_NUMBER
WEBSITE_URL=$WEBSITE_URL
TELEGRAM_CHANNEL=$TELEGRAM_CHANNEL
MAP_COORDINATES=$MAP_COORDINATES
EOL

echo ".env файл создан"

# Инициализация базы данных
echo "Инициализация базы данных..."
python3 -c "
from database import Database
db = Database()
print('База данных создана успешно')
"

echo "Установка завершена!"
echo "Для запуска бота выполните: python3 main.py"
