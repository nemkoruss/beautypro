#!/bin/bash

# Update and upgrade system
echo "Updating system..."
sudo apt update && sudo apt upgrade -y

# Check and install git
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    sudo apt install git -y
fi

# Check and install python3
if ! command -v python3 &> /dev/null; then
    echo "Installing python3..."
    sudo apt install python3 -y
fi

# Check and install pip
if ! command -v pip3 &> /dev/null; then
    echo "Installing pip3..."
    sudo apt install python3-pip -y
fi

# Install requirements
echo "Installing Python packages..."
pip3 install -r requirements.txt

# Create .env file
echo "Creating .env file..."
read -p "Enter BOT_TOKEN: " BOT_TOKEN
read -p "Enter ADMIN_IDS (comma separated): " ADMIN_IDS
read -p "Enter phone number: " PHONE_NUMBER
read -p "Enter website URL: " WEBSITE_URL
read -p "Enter Telegram channel URL: " TELEGRAM_CHANNEL
read -p "Enter location coordinates (lat,lon): " LOCATION_COORDINATES

cat > .env << EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=$ADMIN_IDS
PHONE_NUMBER=$PHONE_NUMBER
WEBSITE_URL=$WEBSITE_URL
TELEGRAM_CHANNEL=$TELEGRAM_CHANNEL
LOCATION_COORDINATES=$LOCATION_COORDINATES
EOF

echo ".env file created successfully!"

# Initialize database
echo "Initializing database..."
python3 -c "
from database import Database
db = Database()
print('Database initialized successfully!')
"

echo "Installation completed! You can now run the bot with: python3 main.py"
