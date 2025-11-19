"""
Простой тест для проверки основных функций бота.
"""

import sys
import database
from database import (
    get_movie_categories, create_movie_category, create_movie, get_movies,
    create_activity, get_activities, 
    get_trip_categories, create_trip_category, create_trip, get_trips,
    create_tiktok_trend, get_tiktok_trends,
    get_photo_categories, create_photo_category,
    create_game, get_games, create_sexual_item, get_sexual_items
)

def test_database():
    """Тест основных функций базы данных."""
    print("[TEST] Тестирование базы данных...")
    
    try:
        # Инициализация
        database.init_database()
        print("[OK] База данных инициализирована")
        
        # Категории фильмов
        categories = get_movie_categories()
        print(f"[OK] Категории фильмов: {len(categories)}")
        assert len(categories) >= 3, "Должно быть минимум 3 категории"
        
        # Тест создания фильма
        category_id = categories[0]['id']
        movie_id = create_movie("Тестовый фильм", "Тестовое примечание", category_id)
        print(f"[OK] Фильм создан: ID={movie_id}")
        
        movies = get_movies(watched=0)
        print(f"[OK] Непросмотренные фильмы: {len(movies)}")
        assert len(movies) > 0, "Должен быть хотя бы один фильм"
        
        # Тест создания активности
        activity_id = create_activity("Тестовая активность", "Тестовое примечание")
        print(f"[OK] Активность создана: ID={activity_id}")
        
        activities = get_activities(status='planned')
        print(f"[OK] Планируемые активности: {len(activities)}")
        assert len(activities) > 0, "Должна быть хотя бы одна активность"
        
        # Тест поездок
        trip_categories = get_trip_categories()
        print(f"[OK] Категории поездок: {len(trip_categories)}")
        assert len(trip_categories) >= 3, "Должно быть минимум 3 категории поездок"
        
        trip_category_id = trip_categories[0]['id']
        trip_id = create_trip("Тестовая поездка", "Тестовое примечание", trip_category_id)
        print(f"[OK] Поездка создана: ID={trip_id}")
        
        trips = get_trips()
        print(f"[OK] Всего поездок: {len(trips)}")
        assert len(trips) > 0, "Должна быть хотя бы одна поездка"
        
        # Тест трендов TikTok
        tiktok_id = create_tiktok_trend("Тестовый тренд", None)
        print(f"[OK] Тренд TikTok создан: ID={tiktok_id}")
        
        tiktok_trends = get_tiktok_trends(status='todo')
        print(f"[OK] Тренды TikTok (todo): {len(tiktok_trends)}")
        assert len(tiktok_trends) > 0, "Должен быть хотя бы один тренд"
        
        # Тест категорий фотографий
        photo_categories = get_photo_categories()
        print(f"[OK] Категории фотографий: {len(photo_categories)}")
        assert len(photo_categories) >= 2, "Должно быть минимум 2 категории фотографий"
        
        photo_cat_id = create_photo_category("Тестовая категория фото", "http://test.com", "Тестовое описание")
        print(f"[OK] Категория фотографий создана: ID={photo_cat_id}")
        
        all_photo_cats = get_photo_categories()
        print(f"[OK] Всего категорий фотографий: {len(all_photo_cats)}")
        assert len(all_photo_cats) > len(photo_categories), "Должна быть добавлена новая категория"
        
        # Тест создания игры
        game_id = create_game("Тестовая игра", "Тестовое примечание", "Тестовый жанр")
        print(f"[OK] Игра создана: ID={game_id}")
        
        games = get_games(status='pending')
        print(f"[OK] Ожидающие игры: {len(games)}")
        assert len(games) > 0, "Должна быть хотя бы одна игра"
        
        # Тест создания sexual записи
        sexual_id = create_sexual_item("Тестовая запись", "http://test.com", "Тестовое описание")
        print(f"[OK] Sexual запись создана: ID={sexual_id}")
        
        sexual_items = get_sexual_items()
        print(f"[OK] Sexual записи: {len(sexual_items)}")
        assert len(sexual_items) > 0, "Должна быть хотя бы одна запись"
        
        print("\n[OK] Все тесты базы данных пройдены успешно!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка в тестах базы данных: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_keyboards():
    """Тест функций клавиатур."""
    print("\n[TEST] Тестирование клавиатур...")
    
    try:
        import keyboards
        
        # Главное меню
        km = keyboards.main_menu_reply_keyboard()
        assert len(km.keyboard) == 4, "Должно быть 4 ряда в главном меню"
        print("[OK] Главное меню (reply): OK")
        
        ik = keyboards.main_menu_inline_keyboard()
        assert len(ik.inline_keyboard) >= 3, "Должно быть минимум 3 ряда в inline меню"
        print("[OK] Главное меню (inline): OK")
        
        # Кнопка назад
        back_kb = keyboards.back_button("test_callback")
        assert len(back_kb.inline_keyboard) == 1, "Должна быть одна кнопка"
        print("[OK] Кнопка назад: OK")
        
        # Список с пагинацией
        test_items = [
            {'id': 1, 'title': 'Тест 1'},
            {'id': 2, 'title': 'Тест 2'},
            {'id': 3, 'title': 'Тест 3'},
        ]
        list_kb = keyboards.list_keyboard(test_items, 0, 10, "test_", "back")
        assert len(list_kb.inline_keyboard) > 0, "Должна быть клавиатура"
        print("[OK] Пагинация: OK")
        
        # Клавиатура оценки
        rating_kb = keyboards.rating_keyboard("rate_", 1, 1)
        assert len(rating_kb.inline_keyboard) >= 2, "Должно быть минимум 2 ряда"
        print("[OK] Клавиатура оценки: OK")
        
        print("\n[OK] Все тесты клавиатур пройдены успешно!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка в тестах клавиатур: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_handlers():
    """Тест импорта обработчиков."""
    print("\n[TEST] Тестирование обработчиков...")
    
    try:
        from handlers import movies, activities, trips, tiktok, photos, games, sexual
        
        # Проверяем, что функции существуют
        assert hasattr(movies, 'register_handlers'), "movies должен иметь register_handlers"
        assert hasattr(activities, 'register_handlers'), "activities должен иметь register_handlers"
        assert hasattr(trips, 'register_handlers'), "trips должен иметь register_handlers"
        assert hasattr(tiktok, 'register_handlers'), "tiktok должен иметь register_handlers"
        assert hasattr(photos, 'register_handlers'), "photos должен иметь register_handlers"
        assert hasattr(games, 'register_handlers'), "games должен иметь register_handlers"
        assert hasattr(sexual, 'register_handlers'), "sexual должен иметь register_handlers"
        
        print("[OK] Все обработчики импортированы успешно")
        print("[OK] Все обработчики имеют функцию register_handlers")
        
        print("\n[OK] Все тесты обработчиков пройдены успешно!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка в тестах обработчиков: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Главная функция тестирования."""
    print("=" * 50)
    print("ЗАПУСК ТЕСТОВ БОТА")
    print("=" * 50)
    
    results = []
    
    # Тесты базы данных
    results.append(test_database())
    
    # Тесты клавиатур
    results.append(test_keyboards())
    
    # Тесты обработчиков
    results.append(test_handlers())
    
    # Итоги
    print("\n" + "=" * 50)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"[OK] Пройдено: {passed}/{total}")
    print(f"[FAIL] Провалено: {total - passed}/{total}")
    
    if all(results):
        print("\n[SUCCESS] ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return 0
    else:
        print("\n[WARNING] НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
        return 1


if __name__ == '__main__':
    sys.exit(main())

