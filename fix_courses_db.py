import sqlite3

def fix_courses_table():
    # Подключаемся к базе данных
    conn = sqlite3.connect('stream_bot.db')
    cursor = conn.cursor()
    
    try:
        # Создаем копию таблицы courses, если она существует
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='courses'")
        if cursor.fetchone():
            print("Создание резервной копии таблицы courses...")
            cursor.execute("ALTER TABLE courses RENAME TO courses_backup")
            
        # Создаем новую таблицу courses
        print("Создание новой таблицы courses...")
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
        
        # Проверяем, что курсы добавлены
        cursor.execute("SELECT COUNT(*) FROM courses")
        count = cursor.fetchone()[0]
        print(f"Добавлено курсов: {count}")
        
        # Выводим список курсов
        cursor.execute("SELECT * FROM courses")
        for course in cursor.fetchall():
            print(f"ID: {course[0]}, Название: {course[1]}, Активен: {course[5]}")
        
        # Сохраняем изменения
        conn.commit()
        print("База данных успешно обновлена!")
        
    except Exception as e:
        conn.rollback()
        print(f"Ошибка: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_courses_table()
