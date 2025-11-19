# ForUs Bot - Telegram Multi-List Bot

Telegram бот для управления списками: фильмы, активности, поездки, тренды TikTok, фотографии, игры и другие записи.

## Установка

### Локальная установка

1. Клонируйте репозиторий:
```bash
git clone <repository_url>
cd ForUs_bot
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Запустите скрипт развертывания:
```bash
python deploy.py
```

4. Заполните конфигурацию:
   - Откройте `.env` и укажите `BOT_TOKEN=ваш_токен_бота`
   - Откройте `config.json` и укажите ID пользователей Telegram

5. Запустите бота:
```bash
python bot.py
```

### Установка через Docker

1. Заполните `.env` и `config.json` как указано выше

2. Запустите через Docker Compose:
```bash
docker-compose up -d
```

3. Просмотр логов:
```bash
docker-compose logs -f
```

## Структура проекта

```
ForUs_bot/
├── bot.py              # Главный файл бота
├── config.py           # Конфигурация
├── database.py         # Работа с БД
├── keyboards.py        # Клавиатуры
├── handlers/           # Обработчики разделов
│   ├── movies.py
│   ├── activities.py
│   ├── trips.py
│   ├── tiktok.py
│   ├── photos.py
│   ├── games.py
│   └── sexual.py
├── deploy.py           # Скрипт развертывания
├── requirements.txt    # Зависимости
├── Dockerfile          # Docker образ
├── docker-compose.yml  # Docker Compose конфигурация
└── data/              # База данных (создается автоматически)
```

## Конфигурация

### .env
```
BOT_TOKEN=your_bot_token_here
```

### config.json
```json
{
  "users": [
    {
      "id": 123456789,
      "name": "User1"
    },
    {
      "id": 987654321,
      "name": "User2"
    }
  ]
}
```

Минимум 2 пользователя обязательно!

## Разделы бота

1. **Фильмы** - управление списком фильмов с категориями, рейтингами и топами
2. **Активности** - планирование и отслеживание активностей
3. **Поездки** - список мест для посещения
4. **Тренды TikTok** - сохранение трендов с видео
5. **Фотографии** - категории фотографий со ссылками
6. **Игры** - список игр с жанрами и рейтингами
7. **Sexual** - приватные записи

## Развертывание на сервере

1. Склонируйте репозиторий на сервер
2. Заполните `.env` и `config.json`
3. Запустите через Docker:
```bash
docker-compose up -d
```

База данных сохраняется в директории `data/` - сделайте резервную копию перед обновлением!

## Развертывание на GitHub

### Быстрая инструкция (PowerShell или Git Bash):

1. Создайте репозиторий на GitHub (без README, .gitignore и лицензии)

2. Выполните команды в папке проекта:
```bash
git init
git add .
git commit -m "Initial commit: ForUs Bot"
git remote add origin https://github.com/yourusername/ForUs_bot.git
git branch -M main
git push -u origin main
```

### Важно перед коммитом

- `.env` и `config.json` **НЕ** попадут в репозиторий (они в .gitignore)
- Используйте `config.json.example` и `.env.example` как шаблоны
- Эти файлы-примеры можно безопасно коммитить

### Клонирование на сервер

На Ubuntu сервере:

```bash
# Клонируем репозиторий
git clone https://github.com/yourusername/ForUs_bot.git
cd ForUs_bot

# Копируем примеры конфигов
cp .env.example .env
cp config.json.example config.json

# Заполняем конфиги
nano .env      # Вставьте BOT_TOKEN
nano config.json  # Вставьте ID пользователей

# Запускаем через Docker
docker-compose up -d
```

## Лицензия

Приватный проект

