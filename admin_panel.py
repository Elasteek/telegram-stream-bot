import os
import logging
import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for, flash
from datetime import datetime

# Настройка логирования для отладки
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'debug_key_123'

# Функция для подключения к базе данных
def get_db_connection():
    conn = sqlite3.connect('stream_bot.db')
    conn.row_factory = sqlite3.Row
    return conn

# Функция для инициализации базы данных
def init_db():
    logger.debug("Инициализация базы данных")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Создаем таблицу стримов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS streams (
        stream_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        stream_date TEXT NOT NULL,
        is_closed INTEGER DEFAULT 0,
        access_link TEXT
    )
    ''')
    
    # Создаем таблицу контента
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS content (
        content_id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        link TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Создаем таблицу цепочек контента
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS content_sequences (
        sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        days_count INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Создаем таблицу элементов цепочки
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sequence_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sequence_id INTEGER NOT NULL,
        content_id INTEGER NOT NULL,
        day_number INTEGER NOT NULL,
        FOREIGN KEY (sequence_id) REFERENCES content_sequences (sequence_id),
        FOREIGN KEY (content_id) REFERENCES content (content_id)
    )
    ''')
    
    # Создаем таблицу подписок пользователей на цепочки
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_sequences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        sequence_id INTEGER NOT NULL,
        current_day INTEGER DEFAULT 0,
        start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (sequence_id) REFERENCES content_sequences (sequence_id)
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.debug("Инициализация базы данных завершена")

# Инициализируем базу данных при запуске
init_db()

# Основные маршруты (существующие)
@app.route('/')
def index():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'admin123':
            session['logged_in'] = True
            session['username'] = username
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Неверное имя пользователя или пароль")
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Количество стримов
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM streams")
    stream_count = cursor.fetchone()[0]
    
    # Количество контента
    cursor.execute("SELECT COUNT(*) FROM content")
    content_count = cursor.fetchone()[0]
    
    # Количество цепочек
    cursor.execute("SELECT COUNT(*) FROM content_sequences")
    sequence_count = cursor.fetchone()[0]
    
    # Ближайшие стримы
    cursor.execute('''SELECT * FROM streams 
                     WHERE stream_date > datetime('now') 
                     ORDER BY stream_date LIMIT 5''')
    streams = cursor.fetchall()
    
    conn.close()
    
    return render_template(
        'dashboard.html', 
        user_count=0,
        stream_count=stream_count, 
        content_count=content_count,
        sequence_count=sequence_count,
        streams=streams
    )

# Маршруты для управления стримами (существующие)
@app.route('/streams')
def streams():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    streams = conn.execute('SELECT * FROM streams ORDER BY stream_date DESC').fetchall()
    conn.close()
    
    return render_template('streams.html', streams=streams)

@app.route('/add_stream', methods=['GET', 'POST'])
def add_stream():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        stream_date = request.form['stream_date']
        is_closed = 1 if 'is_closed' in request.form else 0
        access_link = request.form['access_link'] if is_closed else None
        
        conn = get_db_connection()
        conn.execute('INSERT INTO streams (title, description, stream_date, is_closed, access_link) VALUES (?, ?, ?, ?, ?)',
                    (title, description, stream_date, is_closed, access_link))
        conn.commit()
        conn.close()
        
        flash('Стрим успешно добавлен!', 'success')
        return redirect(url_for('streams'))
    
    return render_template('stream_form.html', title='Добавление стрима')

@app.route('/edit_stream/<int:stream_id>', methods=['GET', 'POST'])
def edit_stream(stream_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    stream = conn.execute('SELECT * FROM streams WHERE stream_id = ?', (stream_id,)).fetchone()
    conn.close()
    
    if not stream:
        flash('Стрим не найден!', 'danger')
        return redirect(url_for('streams'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        stream_date = request.form['stream_date']
        is_closed = 1 if 'is_closed' in request.form else 0
        access_link = request.form['access_link'] if is_closed else None
        
        conn = get_db_connection()
        conn.execute('UPDATE streams SET title = ?, description = ?, stream_date = ?, is_closed = ?, access_link = ? WHERE stream_id = ?',
                    (title, description, stream_date, is_closed, access_link, stream_id))
        conn.commit()
        conn.close()
        
        flash('Стрим успешно обновлен!', 'success')
        return redirect(url_for('streams'))
    
    return render_template('stream_form.html', title='Редактирование стрима', stream=stream)

@app.route('/delete_stream/<int:stream_id>', methods=['POST'])
def delete_stream(stream_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM streams WHERE stream_id = ?', (stream_id,))
    conn.commit()
    conn.close()
    
    flash('Стрим успешно удален!', 'success')
    return redirect(url_for('streams'))

# Маршруты для управления контентом (существующие)
@app.route('/content')
def content():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    content_items = conn.execute('SELECT * FROM content ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return render_template('content.html', content_items=content_items)

@app.route('/add_content', methods=['GET', 'POST'])
def add_content():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        content_type = request.form['content_type']
        title = request.form['title']
        description = request.form['description']
        link = request.form['link']
        
        conn = get_db_connection()
        conn.execute('INSERT INTO content (content_type, title, description, link) VALUES (?, ?, ?, ?)',
                    (content_type, title, description, link))
        conn.commit()
        conn.close()
        
        flash('Контент успешно добавлен!', 'success')
        return redirect(url_for('content'))
    
    return render_template('content_form.html', title='Добавление контента')

@app.route('/edit_content/<int:content_id>', methods=['GET', 'POST'])
def edit_content(content_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    content = conn.execute('SELECT * FROM content WHERE content_id = ?', (content_id,)).fetchone()
    conn.close()
    
    if not content:
        flash('Контент не найден!', 'danger')
        return redirect(url_for('content'))
    
    if request.method == 'POST':
        content_type = request.form['content_type']
        title = request.form['title']
        description = request.form['description']
        link = request.form['link']
        
        conn = get_db_connection()
        conn.execute('UPDATE content SET content_type = ?, title = ?, description = ?, link = ? WHERE content_id = ?',
                    (content_type, title, description, link, content_id))
        conn.commit()
        conn.close()
        
        flash('Контент успешно обновлен!', 'success')
        return redirect(url_for('content'))
    
    return render_template('content_form.html', title='Редактирование контента', content=content)

# НОВЫЕ МАРШРУТЫ ДЛЯ УПРАВЛЕНИЯ ЦЕПОЧКАМИ КОНТЕНТА
@app.route('/sequences')
def sequences():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    sequences = conn.execute('SELECT * FROM content_sequences ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return render_template('sequences.html', sequences=sequences)

@app.route('/add_sequence', methods=['GET', 'POST'])
def add_sequence():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        days_count = int(request.form['days_count'])
        
        conn = get_db_connection()
        conn.execute('INSERT INTO content_sequences (title, description, days_count) VALUES (?, ?, ?)',
                    (title, description, days_count))
        conn.commit()
        
        # Получаем ID созданной цепочки
        sequence_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()
        
        flash('Цепочка контента успешно создана!', 'success')
        return redirect(url_for('edit_sequence', sequence_id=sequence_id))
    
    return render_template('sequence_form.html', title='Создание цепочки контента')

@app.route('/edit_sequence/<int:sequence_id>', methods=['GET', 'POST'])
def edit_sequence(sequence_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    sequence = conn.execute('SELECT * FROM content_sequences WHERE sequence_id = ?', (sequence_id,)).fetchone()
    
    if not sequence:
        conn.close()
        flash('Цепочка контента не найдена!', 'danger')
        return redirect(url_for('sequences'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        days_count = int(request.form['days_count'])
        
        conn.execute('UPDATE content_sequences SET title = ?, description = ?, days_count = ? WHERE sequence_id = ?',
                    (title, description, days_count, sequence_id))
        conn.commit()
        
        flash('Цепочка контента успешно обновлена!', 'success')
        return redirect(url_for('edit_sequence_items', sequence_id=sequence_id))
    
    conn.close()
    return render_template('sequence_form.html', title='Редактирование цепочки контента', sequence=sequence)

@app.route('/edit_sequence_items/<int:sequence_id>', methods=['GET', 'POST'])
def edit_sequence_items(sequence_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    sequence = conn.execute('SELECT * FROM content_sequences WHERE sequence_id = ?', (sequence_id,)).fetchone()
    
    if not sequence:
        conn.close()
        flash('Цепочка контента не найдена!', 'danger')
        return redirect(url_for('sequences'))
    
    # Получаем все элементы цепочки
    items = conn.execute('''
        SELECT si.item_id, si.day_number, c.content_id, c.title, c.content_type
        FROM sequence_items si
        JOIN content c ON si.content_id = c.content_id
        WHERE si.sequence_id = ?
        ORDER BY si.day_number
    ''', (sequence_id,)).fetchall()
    
    # Получаем весь доступный контент
    all_content = conn.execute('SELECT content_id, title, content_type FROM content ORDER BY title').fetchall()
    
    if request.method == 'POST':
        if 'add_item' in request.form:
            content_id = int(request.form['content_id'])
            day_number = int(request.form['day_number'])
            
            # Проверяем, не существует ли уже элемент для этого дня
            existing = conn.execute('''
                SELECT COUNT(*) FROM sequence_items 
                WHERE sequence_id = ? AND day_number = ?
            ''', (sequence_id, day_number)).fetchone()[0]
            
            if existing > 0:
                flash(f'День {day_number} уже содержит контент! Выберите другой день.', 'danger')
            else:
                conn.execute('''
                    INSERT INTO sequence_items (sequence_id, content_id, day_number)
                    VALUES (?, ?, ?)
                ''', (sequence_id, content_id, day_number))
                conn.commit()
                flash('Элемент добавлен в цепочку!', 'success')
                
        elif 'delete_item' in request.form:
            item_id = int(request.form['item_id'])
            conn.execute('DELETE FROM sequence_items WHERE item_id = ?', (item_id,))
            conn.commit()
            flash('Элемент удален из цепочки!', 'success')
    
    # Обновляем список элементов после изменений
    items = conn.execute('''
        SELECT si.item_id, si.day_number, c.content_id, c.title, c.content_type
        FROM sequence_items si
        JOIN content c ON si.content_id = c.content_id
        WHERE si.sequence_id = ?
        ORDER BY si.day_number
    ''', (sequence_id,)).fetchall()
    
    conn.close()
    
    return render_template(
        'sequence_items.html', 
        sequence=sequence, 
        items=items, 
        all_content=all_content,
        title='Настройка цепочки контента'
    )

@app.route('/delete_sequence/<int:sequence_id>', methods=['POST'])
def delete_sequence(sequence_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Сначала удаляем все элементы цепочки
    conn.execute('DELETE FROM sequence_items WHERE sequence_id = ?', (sequence_id,))
    
    # Затем удаляем саму цепочку
    conn.execute('DELETE FROM content_sequences WHERE sequence_id = ?', (sequence_id,))
    
    conn.commit()
    conn.close()
    
    flash('Цепочка контента успешно удалена!', 'success')
    return redirect(url_for('sequences'))

# Заглушка для раздела пользователей
@app.route('/users')
def users():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    flash('Раздел пользователей скоро будет доступен', 'info')
    return redirect(url_for('dashboard'))

# Выход из системы
@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы!', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
