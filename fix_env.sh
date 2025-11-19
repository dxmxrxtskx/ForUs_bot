#!/bin/bash
# Скрипт для исправления кодировки .env файла

echo "Исправление кодировки .env файла..."

# Удаляем старый файл с неправильной кодировкой
if [ -f .env ]; then
    echo "Удаление старого .env файла..."
    rm .env
fi

# Создаем новый файл в правильной кодировке UTF-8
echo "Создание нового .env файла..."
cat > .env << 'EOF'
BOT_TOKEN=your_bot_token_here
EOF

echo ""
echo "Файл .env создан в правильной кодировке!"
echo ""
echo "Теперь отредактируйте файл и вставьте ваш BOT_TOKEN:"
echo "  nano .env"
echo "  или"
echo "  vim .env"
echo ""
echo "Или используйте команду:"
echo "  sed -i 's/your_bot_token_here/ВАШ_ТОКЕН/' .env"

