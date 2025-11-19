#!/bin/bash
# Скрипт для быстрого обновления бота на сервере

cd "$(dirname "$0")"

echo "=========================================="
echo "Обновление ForUs Bot"
echo "=========================================="

# Создание резервной копии БД
if [ -f "data/multilists.db" ]; then
    BACKUP_FILE="data/multilists_backup_$(date +%Y%m%d_%H%M%S).db"
    cp data/multilists.db "$BACKUP_FILE"
    echo "[OK] Резервная копия БД создана: $BACKUP_FILE"
else
    echo "[WARNING] Файл БД не найден, пропускаем резервное копирование"
fi

# Остановка бота
echo ""
echo "Остановка бота..."
docker-compose down

# Обновление кода из GitHub
echo ""
echo "Обновление кода из GitHub..."
git pull

if [ $? -ne 0 ]; then
    echo "[ERROR] Ошибка при обновлении кода!"
    echo "Запускаем бота с текущим кодом..."
    docker-compose up -d
    exit 1
fi

# Пересборка и запуск
echo ""
echo "Пересборка и запуск..."
docker-compose up -d --build

# Проверка статуса
echo ""
echo "Проверка статуса..."
sleep 3

if docker-compose ps | grep -q "Up"; then
    echo "[OK] Бот успешно запущен!"
    echo ""
    echo "Просмотр логов: docker-compose logs -f"
else
    echo "[ERROR] Бот не запустился! Проверьте логи:"
    echo "docker-compose logs"
    exit 1
fi

echo ""
echo "=========================================="
echo "Обновление завершено!"
echo "=========================================="

