import os
import logging
import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for, flash

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
        
        # Простая проверка для тестирования
        if username == 'admin' and password == 'admin123':
            session['logged_in'] = True
            session['username'] = username
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
    
    return render_template(
        'dashboard.html', 
        user_count=0,
        stream_count=0, 
        content_count=0,
        streams=[]
    )

# Заглушки для функций
@app.route('/streams')
def streams():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/add_stream')
def add_stream():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/content')
def content():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/add_content')
def add_content():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/users')
def users():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
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
    app.run(host='0.0.0.0', port=port)
