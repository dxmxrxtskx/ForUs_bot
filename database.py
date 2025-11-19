"""
Модуль для работы с базой данных SQLite.

База данных: data/multilists.db
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List

# Настройка логирования
# logging.getLogger(__name__) - получает логгер с именем текущего модуля
# Это позволяет видеть в логах, откуда пришло сообщение
logger = logging.getLogger(__name__)

# Путь к базе данных
# Path('data/multilists.db') - создает объект Path для работы с путями
# Это современный способ работы с путями в Python (вместо os.path)
DB_PATH = Path('data/multilists.db')


def get_connection() -> sqlite3.Connection:
    """
    Функция 1: Создает и возвращает соединение с базой данных.
    
    Пошаговое объяснение:
    
    Шаг 1: DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        - DB_PATH.parent - получает родительскую директорию (data/)
        - mkdir() - создает директорию
        - parents=True - создает все родительские директории если их нет
        - exist_ok=True - не выдает ошибку, если директория уже существует
        Результат: директория data/ гарантированно существует
    
    Шаг 2: sqlite3.connect(DB_PATH)
        - sqlite3.connect() - стандартная функция Python для подключения к SQLite
        - DB_PATH - путь к файлу БД (data/multilists.db)
        - Если файла нет, SQLite создаст его автоматически
        Результат: объект Connection для работы с БД
    
    Шаг 3: conn.row_factory = sqlite3.Row
        - row_factory - это настройка, которая определяет формат результатов запросов
        - sqlite3.Row - специальный класс, который позволяет обращаться к колонкам:
          * row['title'] - по имени колонки как к словарю
          * row.title - по имени колонки как к атрибуту
          * row[0] - по индексу (как обычно)
        Без этого мы бы получали обычные tuple, что менее удобно
    
    Returns:
        sqlite3.Connection - соединение с БД, готовое к использованию
    """
    # Шаг 1: Создаем директорию data/ если её нет
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Шаг 2: Подключаемся к базе данных
    conn = sqlite3.connect(DB_PATH)
    
    # Шаг 3: Настраиваем формат результатов запросов
    conn.row_factory = sqlite3.Row
    
    return conn


def init_database() -> None:
    """
    Функция 2: Инициализирует базу данных - создает все необходимые таблицы.
    
    Общая структура функции:
    
    Шаг 1: conn = get_connection()
        - Вызываем нашу функцию get_connection() для получения соединения
        - Теперь у нас есть активное соединение с БД
    
    Шаг 2: cursor = conn.cursor()
        - cursor() - создает курсор для выполнения SQL-запросов
        - Курсор - это объект, через который мы выполняем команды SQL
        - Все SQL-команды выполняются через cursor.execute()
    
    Шаг 3: try/except/finally блок
        - try - выполняем все SQL-команды
        - except - если ошибка, откатываем изменения (rollback)
        - finally - всегда закрываем соединение, даже если была ошибка
    
    Шаг 4: conn.commit()
        - commit() - сохраняет все изменения в БД
        - Без commit() изменения не сохранятся (транзакция не завершится)
    
    Шаг 5: conn.close()
        - close() - закрывает соединение с БД
        - Важно всегда закрывать соединения, чтобы освободить ресурсы
    """
    # Шаг 1: Получаем соединение с БД
    conn = get_connection()
    
    # Шаг 2: Создаем курсор для выполнения SQL-запросов
    cursor = conn.cursor()
    
    try:
        # ============================================
        # ТАБЛИЦА 1: movie_categories (категории фильмов)
        # ============================================
        
        # SQL команда CREATE TABLE:
        # - CREATE TABLE - создает новую таблицу
        # - IF NOT EXISTS - безопасно: не выдает ошибку, если таблица уже существует
        # - movie_categories - имя таблицы
        
        # Колонки таблицы:
        # - id INTEGER PRIMARY KEY AUTOINCREMENT
        #   * INTEGER - целое число
        #   * PRIMARY KEY - уникальный идентификатор записи
        #   * AUTOINCREMENT - автоматически увеличивается при каждой новой записи
        #   Пример: первая запись id=1, вторая id=2, и т.д.
        #
        # - title TEXT NOT NULL UNIQUE
        #   * TEXT - текстовое поле
        #   * NOT NULL - обязательно для заполнения (не может быть пустым)
        #   * UNIQUE - значение должно быть уникальным (не может быть двух одинаковых)
        #   Пример: "Фильм", "Сериал", "Мультик"
        #
        # - created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        #   * TIMESTAMP - дата и время
        #   * DEFAULT CURRENT_TIMESTAMP - автоматически ставит текущую дату/время при создании записи
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movie_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Вставляем дефолтные категории (если их еще нет):
        # - default_movie_categories - список названий категорий
        # - for category in ... - перебираем каждую категорию
        # - INSERT OR IGNORE - вставляем запись, но игнорируем ошибку если она уже есть
        #   (благодаря UNIQUE в title)
        # - VALUES (?) - параметризованный запрос (защита от SQL-инъекций)
        # - (category,) - передаем значение (запятая нужна для tuple из одного элемента)
        
        default_movie_categories = ["Фильм", "Сериал", "Мультик"]
        for category in default_movie_categories:
            cursor.execute(
                "INSERT OR IGNORE INTO movie_categories (title) VALUES (?)",
                (category,)
            )
        
        # ============================================
        # ТАБЛИЦА 2: movies (фильмы)
        # ============================================
        
        # Колонки таблицы:
        # - id - уникальный идентификатор (как в предыдущей таблице)
        # - title TEXT NOT NULL - название фильма (обязательно)
        # - note TEXT - примечание (опционально, может быть NULL)
        # - category_id INTEGER NOT NULL - ID категории из таблицы movie_categories
        # - user1_rating INTEGER - оценка первого пользователя (1-10, может быть NULL)
        # - user2_rating INTEGER - оценка второго пользователя (1-10, может быть NULL)
        # - watched INTEGER DEFAULT 0 - флаг просмотра (0=не просмотрен, 1=просмотрен)
        # - created_at - дата создания
        
        # FOREIGN KEY (category_id) REFERENCES movie_categories(id)
        # Это связь между таблицами (реляционная связь):
        # - FOREIGN KEY - внешний ключ (ссылка на другую таблицу)
        # - category_id - колонка в таблице movies
        # - REFERENCES movie_categories(id) - ссылается на колонку id в таблице movie_categories
        # 
        # Что это дает:
        # - Гарантирует, что category_id всегда существует в movie_categories
        # - Нельзя удалить категорию, если на неё ссылаются фильмы
        # - Обеспечивает целостность данных
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                note TEXT,
                category_id INTEGER NOT NULL,
                user1_rating INTEGER,
                user2_rating INTEGER,
                watched INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES movie_categories(id)
            )
        """)
        
        # ============================================
        # ТАБЛИЦА 3: activities (активности)
        # ============================================
        # - status TEXT NOT NULL DEFAULT 'planned'
        #   * DEFAULT 'planned' - значение по умолчанию при создании записи
        #   * Может быть 'planned' (запланировано) или 'done' (выполнено)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                note TEXT,
                status TEXT NOT NULL DEFAULT 'planned',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ============================================
        # ТАБЛИЦА 4: trip_categories (категории поездок)
        # ============================================
        # Аналогично movie_categories - список категорий для поездок
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trip_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Дефолтные категории поездок
        default_trip_categories = ["Пешком", "Поездки", "Места в Херцег-Нови"]
        for category in default_trip_categories:
            cursor.execute(
                "INSERT OR IGNORE INTO trip_categories (title) VALUES (?)",
                (category,)
            )
        
        # ============================================
        # ТАБЛИЦА 5: trips (поездки)
        # ============================================
        # - visited INTEGER DEFAULT 0 - флаг посещения (0=не посещено, 1=посещено)
        # - FOREIGN KEY на trip_categories (как в movies)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                note TEXT,
                category_id INTEGER NOT NULL,
                visited INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES trip_categories(id)
            )
        """)
        
        # ============================================
        # ТАБЛИЦА 6: tiktok_trends (тренды TikTok)
        # ============================================
        # - video_file_id TEXT - ID видео файла в Telegram (для отправки видео)
        #   * Telegram хранит файлы по file_id, можно переиспользовать
        # - status - 'todo' (надо снять) или 'done' (снято)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tiktok_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                video_file_id TEXT,
                status TEXT NOT NULL DEFAULT 'todo',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ============================================
        # ТАБЛИЦА 7: photo_categories (категории фотографий)
        # ============================================
        # - link TEXT - ссылка на альбом/папку с фотографиями
        # - description TEXT - описание категории
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS photo_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                link TEXT,
                description TEXT
            )
        """)
        
        # Дефолтные категории фотографий
        # - Используем tuple для передачи нескольких значений
        # - None означает, что поле будет пустым (NULL в БД)
        default_photo_categories = [
            ("for all", None, None),
            ("not for all", None, None)
        ]
        for title, link, desc in default_photo_categories:
            cursor.execute(
                "INSERT OR IGNORE INTO photo_categories (title, link, description) VALUES (?, ?, ?)",
                (title, link, desc)
            )
        
        # ============================================
        # ТАБЛИЦА 8: games (игры)
        # ============================================
        # - genre TEXT - жанр игры (опционально, может быть NULL)
        # - status - 'pending' (ожидающие) или 'done' (пройденные)
        # - user1_rating, user2_rating - оценки двух пользователей (как в movies)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                note TEXT,
                genre TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                user1_rating INTEGER,
                user2_rating INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ============================================
        # ТАБЛИЦА 9: sexual
        # ============================================
        # Простая таблица без категорий: title, link, description
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sexual (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                link TEXT,
                description TEXT
            )
        """)
        
        # ============================================
        # СОХРАНЕНИЕ ИЗМЕНЕНИЙ
        # ============================================
        # conn.commit() - сохраняет все изменения в БД
        # Без commit() все изменения будут потеряны при закрытии соединения
        # Это называется "транзакция" - либо все изменения сохраняются, либо ничего
        
        conn.commit()
        logger.info("✅ База данных инициализирована успешно")
        
    except sqlite3.Error as e:
        # ============================================
        # ОБРАБОТКА ОШИБОК
        # ============================================
        # except sqlite3.Error - ловим любые ошибки SQLite
        # - logger.error() - записываем ошибку в лог
        # - conn.rollback() - откатываем все изменения (если были)
        #   * rollback() возвращает БД в состояние до начала транзакции
        # - raise - пробрасываем ошибку дальше, чтобы программа знала об ошибке
        
        logger.error(f"❌ Ошибка при инициализации БД: {e}")
        conn.rollback()
        raise
    finally:
        # ============================================
        # ЗАКРЫТИЕ СОЕДИНЕНИЯ
        # ============================================
        # finally - выполняется ВСЕГДА, даже если была ошибка
        # conn.close() - закрывает соединение с БД
        # Важно: всегда закрывать соединения, чтобы освободить ресурсы
        
        conn.close()


# ============================================
# CRUD ОПЕРАЦИИ ДЛЯ РАЗДЕЛА "ФИЛЬМЫ"
# ============================================

def get_movie_categories() -> List[sqlite3.Row]:
    """Получить все категории фильмов."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movie_categories ORDER BY title")
    result = cursor.fetchall()
    conn.close()
    return result


def create_movie_category(title: str) -> int:
    """Создать новую категорию фильмов. Возвращает ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO movie_categories (title) VALUES (?)", (title,))
    conn.commit()
    category_id = cursor.lastrowid
    conn.close()
    return category_id


def get_movies(watched: Optional[int] = None, category_id: Optional[int] = None) -> List[sqlite3.Row]:
    """Получить фильмы. watched: 0=не просмотренные, 1=просмотренные, None=все."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT m.*, mc.title as category_title FROM movies m JOIN movie_categories mc ON m.category_id = mc.id"
    conditions = []
    params = []
    
    if watched is not None:
        conditions.append("m.watched = ?")
        params.append(watched)
    
    if category_id is not None:
        conditions.append("m.category_id = ?")
        params.append(category_id)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY m.created_at DESC"
    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    return result


def get_movie_by_id(movie_id: int) -> Optional[sqlite3.Row]:
    """Получить фильм по ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.*, mc.title as category_title 
        FROM movies m 
        JOIN movie_categories mc ON m.category_id = mc.id 
        WHERE m.id = ?
    """, (movie_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def create_movie(title: str, note: Optional[str], category_id: int) -> int:
    """Создать фильм. Возвращает ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO movies (title, note, category_id) VALUES (?, ?, ?)",
        (title, note, category_id)
    )
    conn.commit()
    movie_id = cursor.lastrowid
    conn.close()
    return movie_id


def update_movie(movie_id: int, title: Optional[str] = None, note: Optional[str] = None) -> None:
    """Обновить фильм."""
    conn = get_connection()
    cursor = conn.cursor()
    updates = []
    params = []
    
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    
    if note is not None:
        updates.append("note = ?")
        params.append(note)
    
    if updates:
        params.append(movie_id)
        cursor.execute(f"UPDATE movies SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    
    conn.close()


def mark_movie_watched(movie_id: int) -> None:
    """Отметить фильм как просмотренный."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE movies SET watched = 1 WHERE id = ?", (movie_id,))
    conn.commit()
    conn.close()


def set_movie_rating(movie_id: int, user_num: int, rating: int) -> None:
    """Установить оценку фильма. user_num: 1 или 2."""
    conn = get_connection()
    cursor = conn.cursor()
    column = f"user{user_num}_rating"
    cursor.execute(f"UPDATE movies SET {column} = ? WHERE id = ?", (rating, movie_id))
    conn.commit()
    conn.close()


def delete_movie(movie_id: int) -> None:
    """Удалить фильм."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
    conn.commit()
    conn.close()


def get_random_movie(exclude_series: bool = True) -> Optional[sqlite3.Row]:
    """Получить случайный фильм. exclude_series=True исключает сериалы."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if exclude_series:
        cursor.execute("""
            SELECT m.*, mc.title as category_title 
            FROM movies m 
            JOIN movie_categories mc ON m.category_id = mc.id 
            WHERE m.watched = 0 AND mc.title != 'Сериал'
            ORDER BY RANDOM()
            LIMIT 1
        """)
    else:
        cursor.execute("""
            SELECT m.*, mc.title as category_title 
            FROM movies m 
            JOIN movie_categories mc ON m.category_id = mc.id 
            WHERE m.watched = 0
            ORDER BY RANDOM()
            LIMIT 1
        """)
    
    result = cursor.fetchone()
    conn.close()
    return result


def get_movies_top(limit: int = 10, user_num: Optional[int] = None) -> List[sqlite3.Row]:
    """Получить топ фильмов. user_num: 1, 2 или None (общий топ по среднему)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if user_num:
        column = f"user{user_num}_rating"
        cursor.execute(f"""
            SELECT m.*, mc.title as category_title, m.{column} as rating
            FROM movies m 
            JOIN movie_categories mc ON m.category_id = mc.id 
            WHERE m.watched = 1 AND m.{column} IS NOT NULL
            ORDER BY m.{column} DESC
            LIMIT ?
        """, (limit,))
    else:
        cursor.execute("""
            SELECT m.*, mc.title as category_title,
                   (COALESCE(m.user1_rating, 0) + COALESCE(m.user2_rating, 0)) / 2.0 as avg_rating
            FROM movies m 
            JOIN movie_categories mc ON m.category_id = mc.id 
            WHERE m.watched = 1 AND m.user1_rating IS NOT NULL AND m.user2_rating IS NOT NULL
            ORDER BY avg_rating DESC
            LIMIT ?
        """, (limit,))
    
    result = cursor.fetchall()
    conn.close()
    return result


# ============================================
# CRUD ОПЕРАЦИИ ДЛЯ РАЗДЕЛА "АКТИВНОСТИ"
# ============================================

def get_activities(status: Optional[str] = None) -> List[sqlite3.Row]:
    """Получить активности. status: 'planned', 'done' или None (все)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if status:
        cursor.execute("SELECT * FROM activities WHERE status = ? ORDER BY created_at DESC", (status,))
    else:
        cursor.execute("SELECT * FROM activities ORDER BY created_at DESC")
    
    result = cursor.fetchall()
    conn.close()
    return result


def get_activity_by_id(activity_id: int) -> Optional[sqlite3.Row]:
    """Получить активность по ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def create_activity(title: str, note: Optional[str]) -> int:
    """Создать активность. Возвращает ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO activities (title, note) VALUES (?, ?)", (title, note))
    conn.commit()
    activity_id = cursor.lastrowid
    conn.close()
    return activity_id


def update_activity(activity_id: int, title: Optional[str] = None, note: Optional[str] = None) -> None:
    """Обновить активность."""
    conn = get_connection()
    cursor = conn.cursor()
    updates = []
    params = []
    
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    
    if note is not None:
        updates.append("note = ?")
        params.append(note)
    
    if updates:
        params.append(activity_id)
        cursor.execute(f"UPDATE activities SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    
    conn.close()


def mark_activity_done(activity_id: int) -> None:
    """Отметить активность как выполненную."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE activities SET status = 'done' WHERE id = ?", (activity_id,))
    conn.commit()
    conn.close()


def delete_activity(activity_id: int) -> None:
    """Удалить активность."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
    conn.commit()
    conn.close()


# ============================================
# CRUD ОПЕРАЦИИ ДЛЯ РАЗДЕЛА "ПОЕЗДКИ"
# ============================================

def get_trip_categories() -> List[sqlite3.Row]:
    """Получить все категории поездок."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trip_categories ORDER BY title")
    result = cursor.fetchall()
    conn.close()
    return result


def create_trip_category(title: str) -> int:
    """Создать новую категорию поездок. Возвращает ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO trip_categories (title) VALUES (?)", (title,))
    conn.commit()
    category_id = cursor.lastrowid
    conn.close()
    return category_id


def get_trips(category_id: Optional[int] = None, visited: Optional[int] = None) -> List[sqlite3.Row]:
    """Получить поездки."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT t.*, tc.title as category_title FROM trips t JOIN trip_categories tc ON t.category_id = tc.id"
    conditions = []
    params = []
    
    if category_id is not None:
        conditions.append("t.category_id = ?")
        params.append(category_id)
    
    if visited is not None:
        conditions.append("t.visited = ?")
        params.append(visited)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY t.created_at DESC"
    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    return result


def get_trip_by_id(trip_id: int) -> Optional[sqlite3.Row]:
    """Получить поездку по ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.*, tc.title as category_title 
        FROM trips t 
        JOIN trip_categories tc ON t.category_id = tc.id 
        WHERE t.id = ?
    """, (trip_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def create_trip(title: str, note: Optional[str], category_id: int) -> int:
    """Создать поездку. Возвращает ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO trips (title, note, category_id) VALUES (?, ?, ?)",
        (title, note, category_id)
    )
    conn.commit()
    trip_id = cursor.lastrowid
    conn.close()
    return trip_id


def update_trip(trip_id: int, title: Optional[str] = None, note: Optional[str] = None) -> None:
    """Обновить поездку."""
    conn = get_connection()
    cursor = conn.cursor()
    updates = []
    params = []
    
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    
    if note is not None:
        updates.append("note = ?")
        params.append(note)
    
    if updates:
        params.append(trip_id)
        cursor.execute(f"UPDATE trips SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    
    conn.close()


def mark_trip_visited(trip_id: int) -> None:
    """Отметить поездку как посещенную."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE trips SET visited = 1 WHERE id = ?", (trip_id,))
    conn.commit()
    conn.close()


def delete_trip(trip_id: int) -> None:
    """Удалить поездку."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    conn.commit()
    conn.close()


# ============================================
# CRUD ОПЕРАЦИИ ДЛЯ РАЗДЕЛА "TIKTOK"
# ============================================

def get_tiktok_trends(status: Optional[str] = None) -> List[sqlite3.Row]:
    """Получить тренды TikTok. status: 'todo', 'done' или None (все)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if status:
        cursor.execute("SELECT * FROM tiktok_trends WHERE status = ? ORDER BY created_at DESC", (status,))
    else:
        cursor.execute("SELECT * FROM tiktok_trends ORDER BY created_at DESC")
    
    result = cursor.fetchall()
    conn.close()
    return result


def get_tiktok_trend_by_id(trend_id: int) -> Optional[sqlite3.Row]:
    """Получить тренд TikTok по ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tiktok_trends WHERE id = ?", (trend_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def create_tiktok_trend(title: str, video_file_id: Optional[str] = None) -> int:
    """Создать тренд TikTok. Возвращает ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tiktok_trends (title, video_file_id) VALUES (?, ?)",
        (title, video_file_id)
    )
    conn.commit()
    trend_id = cursor.lastrowid
    conn.close()
    return trend_id


def mark_tiktok_trend_done(trend_id: int) -> None:
    """Отметить тренд TikTok как выполненный."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tiktok_trends SET status = 'done' WHERE id = ?", (trend_id,))
    conn.commit()
    conn.close()


def delete_tiktok_trend(trend_id: int) -> None:
    """Удалить тренд TikTok."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tiktok_trends WHERE id = ?", (trend_id,))
    conn.commit()
    conn.close()


# ============================================
# CRUD ОПЕРАЦИИ ДЛЯ РАЗДЕЛА "ФОТОГРАФИИ"
# ============================================

def get_photo_categories() -> List[sqlite3.Row]:
    """Получить все категории фотографий."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM photo_categories ORDER BY title")
    result = cursor.fetchall()
    conn.close()
    return result


def get_photo_category_by_id(category_id: int) -> Optional[sqlite3.Row]:
    """Получить категорию фотографий по ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM photo_categories WHERE id = ?", (category_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def create_photo_category(title: str, link: Optional[str] = None, description: Optional[str] = None) -> int:
    """Создать категорию фотографий. Возвращает ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO photo_categories (title, link, description) VALUES (?, ?, ?)",
        (title, link, description)
    )
    conn.commit()
    category_id = cursor.lastrowid
    conn.close()
    return category_id


def update_photo_category(
    category_id: int,
    title: Optional[str] = None,
    link: Optional[str] = None,
    description: Optional[str] = None
) -> None:
    """Обновить категорию фотографий."""
    conn = get_connection()
    cursor = conn.cursor()
    updates = []
    params = []
    
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    
    if link is not None:
        updates.append("link = ?")
        params.append(link)
    
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    
    if updates:
        params.append(category_id)
        cursor.execute(f"UPDATE photo_categories SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    
    conn.close()


def delete_photo_category(category_id: int) -> None:
    """Удалить категорию фотографий."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM photo_categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()


# ============================================
# CRUD ОПЕРАЦИИ ДЛЯ РАЗДЕЛА "ИГРЫ"
# ============================================

def get_games(status: Optional[str] = None, genre: Optional[str] = None) -> List[sqlite3.Row]:
    """Получить игры."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM games"
    conditions = []
    params = []
    
    if status:
        conditions.append("status = ?")
        params.append(status)
    
    if genre:
        conditions.append("genre = ?")
        params.append(genre)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY created_at DESC"
    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    return result


def get_game_by_id(game_id: int) -> Optional[sqlite3.Row]:
    """Получить игру по ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM games WHERE id = ?", (game_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def create_game(title: str, note: Optional[str] = None, genre: Optional[str] = None) -> int:
    """Создать игру. Возвращает ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO games (title, note, genre) VALUES (?, ?, ?)",
        (title, note, genre)
    )
    conn.commit()
    game_id = cursor.lastrowid
    conn.close()
    return game_id


def update_game(
    game_id: int,
    title: Optional[str] = None,
    note: Optional[str] = None,
    genre: Optional[str] = None
) -> None:
    """Обновить игру."""
    conn = get_connection()
    cursor = conn.cursor()
    updates = []
    params = []
    
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    
    if note is not None:
        updates.append("note = ?")
        params.append(note)
    
    if genre is not None:
        updates.append("genre = ?")
        params.append(genre)
    
    if updates:
        params.append(game_id)
        cursor.execute(f"UPDATE games SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    
    conn.close()


def mark_game_done(game_id: int) -> None:
    """Отметить игру как пройденную."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE games SET status = 'done' WHERE id = ?", (game_id,))
    conn.commit()
    conn.close()


def set_game_rating(game_id: int, user_num: int, rating: int) -> None:
    """Установить оценку игры. user_num: 1 или 2."""
    conn = get_connection()
    cursor = conn.cursor()
    column = f"user{user_num}_rating"
    cursor.execute(f"UPDATE games SET {column} = ? WHERE id = ?", (rating, game_id))
    conn.commit()
    conn.close()


def delete_game(game_id: int) -> None:
    """Удалить игру."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM games WHERE id = ?", (game_id,))
    conn.commit()
    conn.close()


def get_random_game() -> Optional[sqlite3.Row]:
    """Получить случайную игру из ожидающих."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM games 
        WHERE status = 'pending'
        ORDER BY RANDOM()
        LIMIT 1
    """)
    result = cursor.fetchone()
    conn.close()
    return result


def get_game_genres() -> List[str]:
    """Получить список всех жанров игр."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT genre FROM games WHERE genre IS NOT NULL ORDER BY genre")
    result = [row['genre'] for row in cursor.fetchall()]
    conn.close()
    return result


def get_games_top(limit: int = 10, user_num: Optional[int] = None) -> List[sqlite3.Row]:
    """Получить топ игр. user_num: 1, 2 или None (общий топ по среднему)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if user_num:
        column = f"user{user_num}_rating"
        cursor.execute(f"""
            SELECT *, {column} as rating
            FROM games 
            WHERE status = 'done' AND {column} IS NOT NULL
            ORDER BY {column} DESC
            LIMIT ?
        """, (limit,))
    else:
        cursor.execute("""
            SELECT *,
                   (COALESCE(user1_rating, 0) + COALESCE(user2_rating, 0)) / 2.0 as avg_rating
            FROM games 
            WHERE status = 'done' AND user1_rating IS NOT NULL AND user2_rating IS NOT NULL
            ORDER BY avg_rating DESC
            LIMIT ?
        """, (limit,))
    
    result = cursor.fetchall()
    conn.close()
    return result


# ============================================
# CRUD ОПЕРАЦИИ ДЛЯ РАЗДЕЛА "SEXUAL"
# ============================================

def get_sexual_items() -> List[sqlite3.Row]:
    """Получить все записи sexual."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sexual ORDER BY id DESC")
    result = cursor.fetchall()
    conn.close()
    return result


def get_sexual_item_by_id(item_id: int) -> Optional[sqlite3.Row]:
    """Получить запись sexual по ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sexual WHERE id = ?", (item_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def create_sexual_item(title: str, link: Optional[str] = None, description: Optional[str] = None) -> int:
    """Создать запись sexual. Возвращает ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sexual (title, link, description) VALUES (?, ?, ?)",
        (title, link, description)
    )
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return item_id


def update_sexual_item(
    item_id: int,
    title: Optional[str] = None,
    link: Optional[str] = None,
    description: Optional[str] = None
) -> None:
    """Обновить запись sexual."""
    conn = get_connection()
    cursor = conn.cursor()
    updates = []
    params = []
    
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    
    if link is not None:
        updates.append("link = ?")
        params.append(link)
    
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    
    if updates:
        params.append(item_id)
        cursor.execute(f"UPDATE sexual SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    
    conn.close()


def delete_sexual_item(item_id: int) -> None:
    """Удалить запись sexual."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sexual WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

