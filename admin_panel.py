import os
import logging
import sqlite3
from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify, g
from datetime import datetime, timedelta
import json
import random

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
    
    # Создаем таблицу пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        phone TEXT,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        FOREIGN KEY (sequence_id) REFERENCES content_sequences (sequence_id),
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    
    # Создаем таблицу истории сообщений с новыми полями
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS message_history (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message_type TEXT NOT NULL,
        text TEXT NOT NULL,
        direction TEXT NOT NULL DEFAULT 'outgoing',
        is_read INTEGER DEFAULT 1,
        reply_to INTEGER,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    
    # Добавляем тестовых пользователей, если таблица пуста
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Генерируем 10 тестовых пользователей
        test_users = [
            (12345, 'user1', 'Иван', 'Иванов', '+7 (900) 123-45-67', (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d %H:%M:%S')),
            (12346, 'user2', 'Петр', 'Петров', '+7 (900) 123-45-68', (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d %H:%M:%S')),
            (12347, 'user3', 'Алексей', 'Смирнов', '+7 (900) 123-45-69', (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d %H:%M:%S')),
            (12348, 'user4', 'Ольга', 'Кузнецова', '+7 (900) 123-45-70', (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d %H:%M:%S')),
            (12349, 'user5', 'Екатерина', 'Иванова', '+7 (900) 123-45-71', (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d %H:%M:%S')),
            (12350, None, 'Николай', 'Соколов', '+7 (900) 123-45-72', (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d %H:%M:%S')),
            (12351, 'user7', 'Мария', 'Попова', '+7 (900) 123-45-73', (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d %H:%M:%S')),
            (12352, 'user8', 'Дмитрий', 'Лебедев', '+7 (900) 123-45-74', (datetime.now() - timedelta(days=random.randint(1, 10))).strftime('%Y-%m-%d %H:%M:%S')),
            (12353, 'user9', 'Анна', 'Козлова', '+7 (900) 123-45-75', (datetime.now() - timedelta(days=random.randint(1, 10))).strftime('%Y-%m-%d %H:%M:%S')),
            (12354, 'user10', 'Сергей', 'Новиков', '+7 (900) 123-45-76', (datetime.now() - timedelta(days=random.randint(1, 5))).strftime('%Y-%m-%d %H:%M:%S')),
        ]
        cursor.executemany('INSERT INTO users (user_id, username, first_name, last_name, phone, registration_date) VALUES (?, ?, ?, ?, ?, ?)', test_users)
        
        # Добавим тестовые сообщения от пользователей для демонстрации
        test_messages = [
            (12345, 'user', 'Здравствуйте! Как мне начать работу с вашим ботом?', 'incoming', 0, None, (datetime.now() - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S')),
            (12346, 'user', 'У меня не получается запустить видео из вашей последней рассылки', 'incoming', 1, None, (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')),
            (12347, 'user', 'Когда будет следующий стрим?', 'incoming', 0, None, (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')),
            (12348, 'user', 'Спасибо за интересный контент!', 'incoming', 1, None, (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')),
        ]
        cursor.executemany('INSERT INTO message_history (user_id, message_type, text, direction, is_read, reply_to, sent_at) VALUES (?, ?, ?, ?, ?, ?, ?)', test_messages)
    
    conn.commit()
    conn.close()
    logger.debug("Инициализация базы данных завершена")

# Инициализируем базу данных при запуске
init_db()

# Функция для получения уведомлений (используется в каждом запросе)
def get_notifications():
    if session.get('logged_in'):
        conn = get_db_connection()
        
        # Получаем количество непрочитанных сообщений
        unread_count = conn.execute('''
            SELECT COUNT(*) FROM message_history 
            WHERE direction = 'incoming' AND is_read = 0
        ''').fetchone()[0]
        
        # Получаем последние 5 непрочитанных сообщений для уведомлений
        notifications = conn.execute('''
            SELECT m.*, u.first_name, u.last_name 
            FROM message_history m
            JOIN users u ON m.user_id = u.user_id
            WHERE m.direction = 'incoming'
            ORDER BY m.is_read ASC, m.sent_at DESC
            LIMIT 5
        ''').fetchall()
        
        conn.close()
        return unread_count, notifications
    return 0, []

# Middleware для добавления данных уведомлений в каждый шаблон
@app.before_request
def before_request():
    if session.get('logged_in'):
        unread_count, notifications = get_notifications()
        g.unread_count = unread_count
        g.notifications = notifications

@app.context_processor
def inject_notifications():
    if session.get('logged_in'):
        return {
            'unread_count': getattr(g, 'unread_count', 0),
            'notifications': getattr(g, 'notifications', [])
        }
    return {'unread_count': 0, 'notifications': []}

# Основные маршруты
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
    
    # Количество пользователей
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    # Количество стримов
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
        user_count=user_count,
        stream_count=stream_count, 
        content_count=content_count,
        sequence_count=sequence_count,
        streams=streams
    )

# Маршруты для управления стримами
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

# Маршруты для управления контентом
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

@app.route('/delete_content/<int:content_id>', methods=['POST'])
def delete_content(content_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM content WHERE content_id = ?', (content_id,))
    conn.commit()
    conn.close()
    
    flash('Контент успешно удален!', 'success')
    return redirect(url_for('content'))

# Маршруты для управления цепочками контента
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
        return redirect(url_for('edit_sequence_items', sequence_id=sequence_id))
    
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

# Маршруты для управления пользователями
@app.route('/users')
def users():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Получаем всех пользователей с количеством активных цепочек и непрочитанных сообщений
    users_data = conn.execute('''
        SELECT u.*, 
               (SELECT COUNT(*) FROM user_sequences us WHERE us.user_id = u.user_id AND us.is_active = 1) AS sequences,
               (SELECT COUNT(*) FROM message_history m WHERE m.user_id = u.user_id AND m.direction = 'incoming' AND m.is_read = 0) AS unread_messages
        FROM users u
        ORDER BY u.registration_date DESC
    ''').fetchall()
    
    # Статистика по новым пользователям
    today = datetime.now().strftime('%Y-%m-%d')
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    new_users_day = conn.execute(
        "SELECT COUNT(*) FROM users WHERE date(registration_date) = ?", 
        (today,)
    ).fetchone()[0]
    
    new_users_week = conn.execute(
        "SELECT COUNT(*) FROM users WHERE date(registration_date) >= ?", 
        (week_ago,)
    ).fetchone()[0]
    
    # Количество активных цепочек
    active_sequences = conn.execute(
        "SELECT COUNT(*) FROM user_sequences WHERE is_active = 1"
    ).fetchone()[0]
    
    conn.close()
    
    return render_template(
        'users.html', 
        users=users_data,
        new_users_day=new_users_day,
        new_users_week=new_users_week,
        active_sequences=active_sequences
    )

@app.route('/user/<int:user_id>')
def user_detail(user_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Получаем информацию о пользователе
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    
    if not user:
        conn.close()
        flash('Пользователь не найден!', 'danger')
        return redirect(url_for('users'))
    
    # Получаем цепочки пользователя
    user_sequences = conn.execute('''
        SELECT us.*, cs.title, cs.days_count
        FROM user_sequences us
        JOIN content_sequences cs ON us.sequence_id = cs.sequence_id
        WHERE us.user_id = ?
        ORDER BY us.start_date DESC
    ''', (user_id,)).fetchall()
    
    # Получаем доступные цепочки для подписки
    available_sequences = conn.execute('''
        SELECT cs.*
        FROM content_sequences cs
        WHERE cs.sequence_id NOT IN (
            SELECT sequence_id FROM user_sequences WHERE user_id = ?
        )
    ''', (user_id,)).fetchall()
    
    # Получаем историю сообщений в формате диалога
    message_history = conn.execute('''
        SELECT *
        FROM message_history
        WHERE user_id = ?
        ORDER BY sent_at DESC
        LIMIT 50
    ''', (user_id,)).fetchall()
    
    # Отмечаем сообщения от этого пользователя как прочитанные
    conn.execute('''
        UPDATE message_history
        SET is_read = 1
        WHERE user_id = ? AND direction = 'incoming' AND is_read = 0
    ''', (user_id,))
    conn.commit()
    
    conn.close()
    
    return render_template(
        'user_detail.html',
        user=user,
        user_sequences=user_sequences,
        available_sequences=available_sequences,
        message_history=message_history
    )

@app.route('/add_user_sequence/<int:user_id>', methods=['POST'])
def add_user_sequence(user_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    sequence_id = request.form.get('sequence_id')
    if not sequence_id:
        flash('Выберите цепочку для подписки!', 'danger')
        return redirect(url_for('user_detail', user_id=user_id))
    
    conn = get_db_connection()
    
    # Проверяем, не подписан ли уже пользователь на эту цепочку
    existing = conn.execute('''
        SELECT COUNT(*) FROM user_sequences 
        WHERE user_id = ? AND sequence_id = ?
    ''', (user_id, sequence_id)).fetchone()[0]
    
    if existing > 0:
        conn.close()
        flash('Пользователь уже подписан на эту цепочку!', 'warning')
        return redirect(url_for('user_detail', user_id=user_id))
    
    # Добавляем подписку
    conn.execute('''
        INSERT INTO user_sequences (user_id, sequence_id, current_day, start_date, is_active)
        VALUES (?, ?, 0, datetime('now'), 1)
    ''', (user_id, sequence_id))
    
    # Добавляем запись о подписке в историю сообщений
    sequence_title = conn.execute('SELECT title FROM content_sequences WHERE sequence_id = ?', (sequence_id,)).fetchone()[0]
    conn.execute('''
        INSERT INTO message_history (user_id, message_type, text, direction)
        VALUES (?, ?, ?, ?)
    ''', (user_id, 'subscription', f"Подписка на цепочку контента: {sequence_title}", 'outgoing'))
    
    conn.commit()
    conn.close()
    
    flash('Пользователь успешно подписан на цепочку!', 'success')
    return redirect(url_for('user_detail', user_id=user_id))

@app.route('/toggle_user_sequence/<int:user_id>/<int:sequence_id>', methods=['POST'])
def toggle_user_sequence(user_id, sequence_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    if 'activate' in request.form:
        conn.execute('''
            UPDATE user_sequences 
            SET is_active = 1
            WHERE user_id = ? AND sequence_id = ?
        ''', (user_id, sequence_id))
        status_message = "активирована"
    else:
        conn.execute('''
            UPDATE user_sequences 
            SET is_active = 0
            WHERE user_id = ? AND sequence_id = ?
        ''', (user_id, sequence_id))
        status_message = "приостановлена"
    
    # Получаем название цепочки для сообщения
    sequence_title = conn.execute('SELECT title FROM content_sequences WHERE sequence_id = ?', (sequence_id,)).fetchone()[0]
    
    # Добавляем запись в историю сообщений
    conn.execute('''
        INSERT INTO message_history (user_id, message_type, text, direction)
        VALUES (?, ?, ?, ?)
    ''', (user_id, 'system', f"Цепочка '{sequence_title}' {status_message}", 'outgoing'))
    
    conn.commit()
    conn.close()
    
    flash(f'Статус цепочки изменен: {status_message}!', 'success')
    return redirect(url_for('user_detail', user_id=user_id))

@app.route('/send_message', methods=['GET', 'POST'])
def send_message():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        recipient_type = request.form.get('recipient_type')
        message_text = request.form.get('message_text')
        reply_to = request.form.get('reply_to')
        
        if not message_text:
            flash('Введите текст сообщения!', 'danger')
            return redirect(url_for('send_message'))
        
        # Определяем список получателей
        recipients = []
        
        if recipient_type == 'all':
            # Все пользователи
            recipients = conn.execute('SELECT user_id FROM users').fetchall()
        
        elif recipient_type == 'sequence':
            # Пользователи конкретной цепочки
            sequence_id = request.form.get('sequence_id')
            if sequence_id:
                recipients = conn.execute('''
                    SELECT user_id FROM user_sequences 
                    WHERE sequence_id = ? AND is_active = 1
                ''', (sequence_id,)).fetchall()
            else:
                flash('Выберите цепочку для отправки!', 'danger')
                return redirect(url_for('send_message'))
        
        elif recipient_type == 'selected':
            # Выбранные пользователи
            user_ids = request.form.getlist('user_ids')
            if user_ids:
                placeholders = ','.join(['?'] * len(user_ids))
                recipients = conn.execute(f'SELECT user_id FROM users WHERE user_id IN ({placeholders})', user_ids).fetchall()
            else:
                flash('Выберите хотя бы одного пользователя!', 'danger')
                return redirect(url_for('send_message'))
        
        elif recipient_type == 'specific':
            # Конкретный пользователь
            user_id = request.form.get('user_id')
            if user_id:
                recipients = [{'user_id': user_id}]
            else:
                flash('Пользователь не найден!', 'danger')
                return redirect(url_for('send_message'))
        
        # Отправляем сообщения и записываем их в историю
        sent_count = 0
        for recipient in recipients:
            user_id = recipient['user_id']
            
            # В реальном приложении здесь был бы код для отправки сообщения через Telegram API
            
            # Записываем сообщение в историю
            conn.execute('''
                INSERT INTO message_history (user_id, message_type, text, direction, reply_to)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, 'manual', message_text, 'outgoing', reply_to))
            
            sent_count += 1
        
        conn.commit()
        
        flash(f'Сообщение успешно отправлено {sent_count} пользователям!', 'success')
        
        # Перенаправляем на предыдущую страницу
        if recipient_type == 'specific':
            return redirect(url_for('user_detail', user_id=user_id))
        else:
            return redirect(url_for('users'))
    
    # Для GET-запроса
    users = conn.execute('SELECT user_id, username, first_name, last_name FROM users ORDER BY first_name, last_name').fetchall()
    
    # Получаем цепочки с количеством подписчиков
    sequences = conn.execute('''
        SELECT cs.sequence_id, cs.title, COUNT(us.id) as subscriber_count
        FROM content_sequences cs
        LEFT JOIN user_sequences us ON cs.sequence_id = us.sequence_id AND us.is_active = 1
        GROUP BY cs.sequence_id
        ORDER BY cs.title
    ''').fetchall()
    
    total_users = len(users)
    
    # Проверяем, отправляем ли сообщение конкретному пользователю
    user_id = request.args.get('user_id')
    specific_user = None
    
    if user_id:
        specific_user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    
    conn.close()
    
    return render_template(
        'send_message.html',
        users=users,
        sequences=sequences,
        total_users=total_users,
        specific_user=specific_user
    )

@app.route('/send_message_to_user/<int:user_id>', methods=['GET', 'POST'])
def send_message_to_user(user_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        message_text = request.form.get('message_text')
        reply_to = request.form.get('reply_to')
        
        if not message_text:
            flash('Введите текст сообщения!', 'danger')
            return redirect(url_for('user_detail', user_id=user_id))
        
        conn = get_db_connection()
        
        # Записываем сообщение в историю
        conn.execute('''
            INSERT INTO message_history (user_id, message_type, text, direction, reply_to)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, 'manual', message_text, 'outgoing', reply_to))
        conn.commit()
        conn.close()
        
        # В реальном приложении здесь был бы код для отправки сообщения через Telegram API
        
        flash('Сообщение успешно отправлено!', 'success')
        return redirect(url_for('user_detail', user_id=user_id))
    
    return redirect(url_for('send_message', user_id=user_id))

# Новые маршруты для работы с сообщениями
@app.route('/all_messages')
def all_messages():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Получаем входящие сообщения от пользователей
    messages = conn.execute('''
        SELECT m.*, u.first_name, u.last_name
        FROM message_history m
        JOIN users u ON m.user_id = u.user_id
        WHERE m.direction = 'incoming'
        ORDER BY m.is_read ASC, m.sent_at DESC
        LIMIT 100
    ''').fetchall()
    
    conn.close()
    
    return render_template('all_messages.html', messages=messages)

@app.route('/mark_message_read/<int:message_id>', methods=['POST'])
def mark_message_read(message_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Получаем user_id сообщения для перенаправления
    user_id = conn.execute('SELECT user_id FROM message_history WHERE message_id = ?', (message_id,)).fetchone()
    
    if user_id:
        user_id = user_id['user_id']
        
        # Отмечаем сообщение как прочитанное
        conn.execute('UPDATE message_history SET is_read = 1 WHERE message_id = ?', (message_id,))
        conn.commit()
        
        flash('Сообщение отмечено как прочитанное', 'success')
    else:
        flash('Сообщение не найдено', 'danger')
    
    conn.close()
    
    # Определяем, откуда пришел запрос
    referrer = request.referrer
    if referrer and 'all_messages' in referrer:
        return redirect(url_for('all_messages'))
    elif user_id:
        return redirect(url_for('user_detail', user_id=user_id))
    else:
        return redirect(url_for('dashboard'))

@app.route('/mark_messages_read/<int:user_id>', methods=['POST'])
def mark_messages_read(user_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Отмечаем все сообщения пользователя как прочитанные
    conn.execute('''
        UPDATE message_history 
        SET is_read = 1 
        WHERE user_id = ? AND direction = 'incoming' AND is_read = 0
    ''', (user_id,))
    
    conn.commit()
    conn.close()
    
    flash('Все сообщения отмечены как прочитанные', 'success')
    
    return redirect(url_for('user_detail', user_id=user_id))

# API для проверки новых сообщений
@app.route('/check_notifications')
def check_notifications():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    unread_count, _ = get_notifications()
    
    return jsonify({
        'unread_count': unread_count
    })

# API для получения сообщений от бота (имитация Telegram)
@app.route('/api/bot/receive_message', methods=['POST'])
def receive_message():
    # Эта функция будет вызываться Telegram ботом когда пользователь отправляет сообщение
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400
    
    user_id = data.get('user_id')
    text = data.get('text')
    
    if not user_id or not text:
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = get_db_connection()
    
    # Проверяем, существует ли пользователь
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    
    if not user:
        # Создаем пользователя, если его нет
        first_name = data.get('first_name', 'Unknown')
        last_name = data.get('last_name', '')
        username = data.get('username')
        
        conn.execute('''
            INSERT INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
    
    # Записываем сообщение в историю
    conn.execute('''
        INSERT INTO message_history (user_id, message_type, text, direction, is_read)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, 'user', text, 'incoming', 0))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/statistics')
def statistics():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Общая статистика
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    content_count = conn.execute("SELECT COUNT(*) FROM content").fetchone()[0]
    sequence_count = conn.execute("SELECT COUNT(*) FROM content_sequences").fetchone()[0]
    stream_count = conn.execute("SELECT COUNT(*) FROM streams").fetchone()[0]
    
    # Статистика регистраций по дням (за последние 30 дней)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    registrations = conn.execute('''
        SELECT date(registration_date) as reg_date, COUNT(*) as count
        FROM users
        WHERE date(registration_date) >= ?
        GROUP BY date(registration_date)
        ORDER BY date(registration_date)
    ''', (thirty_days_ago,)).fetchall()
    
    registration_dates = [row['reg_date'] for row in registrations]
    registration_counts = [row['count'] for row in registrations]
    
    # Популярность цепочек
    sequences = conn.execute('''
        SELECT cs.title, COUNT(us.id) as subscriber_count
        FROM content_sequences cs
        LEFT JOIN user_sequences us ON cs.sequence_id = us.sequence_id
        GROUP BY cs.sequence_id
        ORDER BY subscriber_count DESC
        LIMIT 5
    ''').fetchall()
    
    sequence_names = [row['title'] for row in sequences]
    sequence_subscribers = [row['subscriber_count'] for row in sequences]
    
    # Статистика отправленных сообщений по типам (за последние 30 дней)
    message_stats = conn.execute('''
        SELECT date(sent_at) as msg_date,
               SUM(CASE WHEN message_type = 'stream' THEN 1 ELSE 0 END) as stream_count,
               SUM(CASE WHEN message_type = 'sequence' THEN 1 ELSE 0 END) as sequence_count,
               SUM(CASE WHEN message_type = 'manual' THEN 1 ELSE 0 END) as manual_count
        FROM message_history
        WHERE date(sent_at) >= ? AND direction = 'outgoing'
        GROUP BY date(sent_at)
        ORDER BY date(sent_at)
    ''', (thirty_days_ago,)).fetchall()
    
    message_dates = [row['msg_date'] for row in message_stats]
    stream_messages = [row['stream_count'] for row in message_stats]
    sequence_messages = [row['sequence_count'] for row in message_stats]
    manual_messages = [row['manual_count'] for row in message_stats]
    
    # Статистика по обратной связи
    feedback_stats = conn.execute('''
        SELECT date(sent_at) as msg_date, COUNT(*) as count
        FROM message_history
        WHERE date(sent_at) >= ? AND direction = 'incoming'
        GROUP BY date(sent_at)
        ORDER BY date(sent_at)
    ''', (thirty_days_ago,)).fetchall()
    
    feedback_dates = [row['msg_date'] for row in feedback_stats]
    feedback_counts = [row['count'] for row in feedback_stats]
    
    conn.close()
    
    return render_template(
        'statistics.html',
        user_count=user_count,
        content_count=content_count,
        sequence_count=sequence_count,
        stream_count=stream_count,
        registration_dates=registration_dates,
        registration_counts=registration_counts,
        sequence_names=sequence_names,
        sequence_subscribers=sequence_subscribers,
        message_dates=message_dates,
        stream_messages=stream_messages,
        sequence_messages=sequence_messages,
        manual_messages=manual_messages,
        feedback_dates=feedback_dates,
        feedback_counts=feedback_counts
    )

# Выход из системы
@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы!', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
