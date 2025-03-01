import sqlite3

def fix_courses_table():
    conn = sqlite3.connect('stream_bot.db')
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли таблица courses
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='courses'")
        if not cursor.fetchone():
            print("Таблица courses не существует. Создаем...")
            
            # Создаем таблицу courses
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                link TEXT NOT NULL,
                order_num INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
        
        # Проверяем, есть ли записи в таблице courses
        cursor.execute("SELECT COUNT(*) FROM courses")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("Таблица courses пуста. Добавляем стандартные курсы...")
            
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
        
        # Убедимся, что все курсы активны
        cursor.execute("UPDATE courses SET is_active = 1")
        
        conn.commit()
        print("Таблица courses успешно обновлена!")
        
        # Выведем список курсов
        cursor.execute("SELECT * FROM courses")
        courses = cursor.fetchall()
        print(f"Количество курсов: {len(courses)}")
        for course in courses:
            print(f"ID: {course[0]}, Название: {course[1]}, Активен: {course[5]}")
        
    except Exception as e:
        conn.rollback()
        print(f"Ошибка: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_courses_table()
