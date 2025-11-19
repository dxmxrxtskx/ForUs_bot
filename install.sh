#!/bin/bash
# Скрипт полной установки ForUs Bot на Ubuntu сервере

set -e  # Останавливаем при ошибке

echo "=========================================="
echo "Установка ForUs Bot"
echo "=========================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода ошибок
error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Функция для вывода успешных сообщений
success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

# Функция для вывода предупреждений
warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Проверка, что скрипт запущен от root или с sudo
if [ "$EUID" -ne 0 ]; then 
    warning "Рекомендуется запускать от root. Некоторые команды могут потребовать sudo."
fi

# Шаг 1: Проверка и установка Docker
echo ""
echo "Шаг 1: Проверка Docker..."

if ! command -v docker &> /dev/null; then
    warning "Docker не установлен. Устанавливаем..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    success "Docker установлен"
else
    success "Docker уже установлен: $(docker --version)"
fi

# Добавляем текущего пользователя в группу docker
if [ "$EUID" -eq 0 ]; then
    USER=$(who am i | awk '{print $1}')
    if [ -n "$USER" ] && [ "$USER" != "root" ]; then
        usermod -aG docker "$USER" 2>/dev/null || true
    fi
fi

# Шаг 2: Проверка и установка Docker Compose
echo ""
echo "Шаг 2: Проверка Docker Compose..."

if ! command -v docker-compose &> /dev/null; then
    warning "Docker Compose не установлен. Устанавливаем..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    success "Docker Compose установлен: $(docker-compose --version)"
else
    success "Docker Compose уже установлен: $(docker-compose --version)"
fi

# Шаг 3: Переход в домашнюю директорию
echo ""
echo "Шаг 3: Подготовка директории..."

cd ~

# Удаляем старую установку (если есть)
if [ -d "ForUs_bot" ]; then
    warning "Найдена старая установка. Удаляем..."
    cd ForUs_bot
    docker-compose down -v --remove-orphans 2>/dev/null || true
    cd ..
    rm -rf ForUs_bot
    success "Старая установка удалена"
fi

# Шаг 4: Клонирование репозитория
echo ""
echo "Шаг 4: Клонирование репозитория..."

read -p "Введите URL репозитория GitHub (или Enter для пропуска): " REPO_URL

if [ -z "$REPO_URL" ]; then
    warning "Пропущено клонирование. Убедитесь, что код уже в ~/ForUs_bot"
    if [ ! -d "ForUs_bot" ]; then
        error "Директория ForUs_bot не найдена!"
    fi
else
    git clone "$REPO_URL" ForUs_bot || error "Ошибка клонирования репозитория"
    success "Репозиторий клонирован"
fi

cd ForUs_bot || error "Не удалось перейти в директорию ForUs_bot"

# Шаг 5: Создание конфигурационных файлов
echo ""
echo "Шаг 5: Создание конфигурационных файлов..."

# Создаем .env файл
if [ ! -f ".env" ]; then
    echo ""
    read -p "Введите BOT_TOKEN от BotFather: " BOT_TOKEN
    if [ -z "$BOT_TOKEN" ]; then
        error "BOT_TOKEN не может быть пустым!"
    fi
    
    # Создаем файл правильным способом (UTF-8 без BOM)
    printf "BOT_TOKEN=%s\n" "$BOT_TOKEN" > .env
    success ".env файл создан"
else
    warning ".env файл уже существует. Проверьте содержимое: cat .env"
fi

# Создаем config.json если его нет
if [ ! -f "config.json" ]; then
    echo ""
    warning "Создание config.json..."
    read -p "Введите Telegram ID первого пользователя: " USER1_ID
    read -p "Введите имя первого пользователя: " USER1_NAME
    
    read -p "Введите Telegram ID второго пользователя: " USER2_ID
    read -p "Введите имя второго пользователя: " USER2_NAME
    
    if [ -z "$USER1_ID" ] || [ -z "$USER2_ID" ]; then
        error "ID пользователей не могут быть пустыми!"
    fi
    
    cat > config.json << EOF
{
  "users": [
    {
      "id": $USER1_ID,
      "name": "$USER1_NAME"
    },
    {
      "id": $USER2_ID,
      "name": "$USER2_NAME"
    }
  ]
}
EOF
    success "config.json создан"
else
    warning "config.json уже существует. Проверьте содержимое: cat config.json"
fi

# Шаг 6: Создание директории для БД
echo ""
echo "Шаг 6: Создание директорий..."

mkdir -p data
chmod 777 data
success "Директория data создана"

# Шаг 7: Очистка старых контейнеров и образов
echo ""
echo "Шаг 7: Очистка старых контейнеров..."

docker-compose down -v --remove-orphans 2>/dev/null || true
docker image prune -f 2>/dev/null || true
success "Очистка завершена"

# Шаг 8: Сборка и запуск
echo ""
echo "Шаг 8: Сборка и запуск бота..."

docker-compose build --no-cache || error "Ошибка сборки образа"
success "Образ собран"

docker-compose up -d || error "Ошибка запуска контейнера"
success "Контейнер запущен"

# Шаг 9: Проверка статуса
echo ""
echo "Шаг 9: Проверка статуса..."

sleep 5

if docker-compose ps | grep -q "Up"; then
    success "Бот запущен успешно!"
else
    error "Бот не запустился. Проверьте логи: docker-compose logs"
fi

# Финальная информация
echo ""
echo "=========================================="
echo -e "${GREEN}Установка завершена!${NC}"
echo "=========================================="
echo ""
echo "Полезные команды:"
echo "  docker-compose logs -f          # Просмотр логов"
echo "  docker-compose ps               # Статус контейнера"
echo "  docker-compose restart          # Перезапуск бота"
echo "  docker-compose stop             # Остановка бота"
echo "  docker-compose down             # Остановка и удаление контейнера"
echo ""
echo "Для обновления:"
echo "  cd ~/ForUs_bot"
echo "  docker-compose down"
echo "  git pull"
echo "  docker-compose build --no-cache"
echo "  docker-compose up -d"
echo ""

