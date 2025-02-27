import os
import logging
import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
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
    
    # Создаем таблицу администраторов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    ''')
    
    # Проверяем, есть ли уже админ
    cursor.execute("SELECT COUNT(*) FROM admins")
    admin_count = cursor.fetchone()[0]
    
    # Если нет, создаем по умолчанию
    if admin_count == 0:
        logger.debug("Создание админа по умолчанию")
        cursor.execute(
            "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
            ('admin', generate_password_hash('admin123'))
        )
    
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
    
    conn.commit()
    conn.close()
    logger.debug("Инициализация базы данных завершена")

# Инициализируем базу данных при запуске
init_db()

# Главная страница - перенаправляет на дашборд или логин
@app.route('/')
def index():
    logger.debug("Запрос к корневому маршруту /")
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    logger.debug(f"Запрос к /login, метод: {request.method}")
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        logger.debug(f"Попытка входа: username={username}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM admins WHERE username = ?", (username,))
        admin = cursor.fetchone()
        conn.close()
        
        if admin and check_password_hash(admin['password_hash'], password):
            session['logged_in'] = True
            session['username'] = username
            session['admin_id'] = admin['id']
            flash('Вы успешно вошли в систему!', 'success')
            logger.debug("Вход успешен, перенаправление на дашборд")
            return redirect(url_for('dashboard'))
        else:
            logger.debug("Ошибка входа - неверные учетные данные")
            return render_template('login.html', error="Неверное имя пользователя или пароль")
    
    logger.debug("Отображение формы входа")
    return render_template('login.html')

# Дашборд
@app.route('/dashboard')
def dashboard():
    logger.debug("Запрос к /dashboard")
    if not session.get('logged_in'):
        logger.debug("Перенаправление на страницу входа - пользователь не вошел в систему")
        return redirect(url_for('login'))
    
    # Получаем статистику
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
    
    # Ближайшие стримы
    cursor.execute("""
    SELECT * FROM streams 
    WHERE stream_date > datetime('now') 
    ORDER BY stream_date 
    LIMIT 5
    """)
    streams = cursor.fetchall()
    
    conn.close()
    
    return render_template(
        'dashboard.html', 
        user_count=user_count,
        stream_count=stream_count,
        content_count=content_count,
        streams=streams
    )

# Заглушки для функций, которые будем реализовывать
@app.route('/streams')
def streams():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    flash('Раздел стримов скоро будет доступен', 'info')
    return redirect(url_for('dashboard'))

@app.route('/add_stream')
def add_stream():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    flash('Функция добавления стримов скоро будет доступна', 'info')
    return redirect(url_for('dashboard'))

@app.route('/content')
def content():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    flash('Раздел контента скоро будет доступен', 'info')
    return redirect(url_for('dashboard'))

@app.route('/add_content')
def add_content():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    flash('Функция добавления контента скоро будет доступна', 'info')
    return redirect(url_for('dashboard'))

@app.route('/users')
def users():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    flash('Раздел пользователей скоро будет доступен', 'info')
    return redirect(url_for('dashboard'))

# Выход из системы
@app.route('/logout')
def logout():
    logger.debug("Выход из системы")
    session.clear()
    flash('Вы вышли из системы!', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Запуск приложения на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
