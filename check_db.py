import sqlite3
import os

DB_PATH = 'stream_bot.db'

def print_separator():
    print('-' * 60)

def check_database():
    print('Диагностика базы данных:')
    print_separator()
    
    # Проверяем, существует ли файл базы данных
    if not os.path.exists(DB_PATH):
        print(f"ОШИБКА: Файл базы данных {DB_PATH} не найден!")
        return False
    
    print(f"Файл базы данных {DB_PATH} существует.")
    
    # Подключаемся к базе данных
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Получаем список всех таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"Найдено таблиц в базе данных: {len(tables)}")
        print("Список таблиц:")
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} записей")
        
        print_separator()
        
        # Проверяем таблицу courses
        if ('courses',) in tables:
            print("Детальная проверка таблицы courses:")
            
            # Получаем структуру таблицы
            cursor.execute("PRAGMA table_info(courses)")
            columns = cursor.fetchall()
            print(f"Количество столбцов: {len(columns)}")
            print("Структура таблицы:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Проверяем содержимое таблицы
            cursor.execute("SELECT * FROM courses")
            courses = cursor.fetchall()
            print(f"Количество курсов: {len(courses)}")
            
            if len(courses) > 0:
                print("Список курсов:")
                for course in courses:
                    print(f"  - ID: {course[0]}, Название: {course[1]}, Активен: {course[5]}")
            else:
                print("ПРЕДУПРЕЖДЕНИЕ: Таблица courses пуста!")
                
                # Добавляем стандартные курсы
                print("Добавление стандартных курсов...")
                default_courses = [
                    ("Для начинающих - Основы музыкального продюсирования", 
                     "Базовый курс для всех, кто хочет начать создавать электронную музыку", 
                     "https://www.flatloops.ru/osnovy_muzykalnogo_prodyusirovaniya", 1, 1),
                    ("Продвинутый курс - Создание техно-трека: от идеи до работы с лейблами", 
                     "Для тех, кто хочет углубить свои знания и научиться работать с лейблами", 
                     "https://www.flatloops.ru/education/online-group/sozdanie-tehno-treka-ot-idei-do-masteringa", 2, 1),
                    ("Продвинутый курс - Техника live выступлений: играй вживую свои треки", 
                     "Научитесь выступать вживую и представлять свою музыку публике", 
                     "https://www.flatloops.ru/education/online-group/tehnika-live-vystuplenij", 3, 1)
                ]
                
                cursor.executemany('''
                    INSERT INTO courses (title, description, link, order_num, is_active) 
                    VALUES (?, ?, ?, ?, ?)
                ''', default_courses)
                
                conn.commit()
                print("Стандартные курсы добавлены.")
        else:
            print("ОШИБКА: Таблица courses не найдена!")
            
            # Создаем таблицу courses
            print("Создание таблицы courses...")
            cursor.execute('''
            CREATE TABLE courses (
                course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                link TEXT NOT NULL,
                order_num INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Добавляем стандартные курсы
            default_courses = [
                ("Для начинающих - Основы музыкального продюсирования", 
                 "Базовый курс для всех, кто хочет начать создавать электронную музыку", 
                 "https://www.flatloops.ru/osnovy_muzykalnogo_prodyusirovaniya", 1, 1),
                ("Продвинутый курс - Создание техно-трека: от идеи до работы с лейблами", 
                 "Для тех, кто хочет углубить свои знания и научиться работать с лейблами", 
                 "https://www.flatloops.ru/education/online-group/sozdanie-tehno-treka-ot-idei-do-masteringa", 2, 1),
                ("Продвинутый курс - Техника live выступлений: играй вживую свои треки", 
                 "Научитесь выступать вживую и представлять свою музыку публике", 
                 "https://www.flatloops.ru/education/online-group/tehnika-live-vystuplenij", 3, 1)
            ]
            
            cursor.executemany('''
                INSERT INTO courses (title, description, link, order_num, is_active) 
                VALUES (?, ?, ?, ?, ?)
            ''', default_courses)
            
            conn.commit()
            print("Таблица courses создана и заполнена стандартными курсами.")
        
        conn.close()
        return True
    
    except Exception as e:
        print(f"ОШИБКА при проверке базы данных: {e}")
        return False

if __name__ == "__main__":
    check_database()
