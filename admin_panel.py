from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField, DateTimeField
from wtforms.validators import DataRequired, Optional, URL
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
csrf = CSRFProtect(app)

# Функция для подключения к базе данных
def get_db_connection():
    conn = sqlite3.connect('stream_bot.db')
    conn.row_factory = sqlite3.Row
    return conn

# Функция для проверки авторизации
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Инициализация базы данных
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Создание таблицы администраторов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    ''')
    
    # Проверка наличия администратора
    cursor.execute("SELECT COUNT(*) FROM admins")
    admin_count = cursor.fetchone()[0]
    
    # Создание администратора по умолчанию
    if admin_count == 0:
        default_username = 'admin'
        default_password = 'admin123'
        password_hash = generate_password_hash(default_password)
        
        cursor.execute(
            "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
            (default_username, password_hash)
        )
        
        print(f"Создана учетная запись администратора: пользователь: {default_username}, пароль: {default_password}")
    
    # Создание таблицы стримов
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
    
    # Создание таблицы контента
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
    
    # Создание таблицы пользователей (если еще не создана)
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

# Форма входа
class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

# Маршруты
@app.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM admins WHERE username = ?", (username,))
        admin = cursor.fetchone()
        conn.close()
        
        if admin and check_password_hash(admin['password_hash'], password):
            session['logged_in'] = True
            session['username'] = username
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверное имя пользователя или пароль!', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы!', 'info')
    return redirect(url_for('login'))

# Управление стримами
@app.route('/streams')
@login_required
def streams():
    conn = get_db_connection()
    streams = conn.execute('SELECT * FROM streams ORDER BY stream_date DESC').fetchall()
    conn.close()
    return render_template('streams.html', streams=streams)

@app.route('/streams/add', methods=['GET', 'POST'])
@login_required
def add_stream():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        stream_date = request.form['stream_date']
        is_closed = 1 if 'is_closed' in request.form else 0
        access_link = request.form['access_link'] if is_closed else None
        
        # Проверка заполнения обязательных полей
        if not title or not stream_date:
            flash('Название и дата стрима обязательны для заполнения!', 'danger')
            return render_template('stream_form.html', title='Добавление стрима')
        
        conn = get_db_connection()
        conn.execute('INSERT INTO streams (title, description, stream_date, is_closed, access_link) VALUES (?, ?, ?, ?, ?)',
                     (title, description, stream_date, is_closed, access_link))
        conn.commit()
        conn.close()
        
        flash('Стрим успешно добавлен!', 'success')
        return redirect(url_for('streams'))
    
    return render_template('stream_form.html', title='Добавление стрима')

@app.route('/streams/edit/<int:stream_id>', methods=['GET', 'POST'])
@login_required
def edit_stream(stream_id):
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
        
        # Проверка заполнения обязательных полей
        if not title or not stream_date:
            flash('Название и дата стрима обязательны для заполнения!', 'danger')
            return render_template('stream_form.html', title='Редактирование стрима', stream=stream)
        
        conn = get_db_connection()
        conn.execute('UPDATE streams SET title = ?, description = ?, stream_date = ?, is_closed = ?, access_link = ? WHERE stream_id = ?',
                     (title, description, stream_date, is_closed, access_link, stream_id))
        conn.commit()
        conn.close()
        
        flash('Стрим успешно обновлен!', 'success')
        return redirect(url_for('streams'))
    
    return render_template('stream_form.html', title='Редактирование стрима', stream=stream)

@app.route('/streams/delete/<int:stream_id>', methods=['POST'])
@login_required
def delete_stream(stream_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM streams WHERE stream_id = ?', (stream_id,))
    conn.commit()
    conn.close()
    
    flash('Стрим успешно удален!', 'success')
    return redirect(url_for('streams'))

# Управление контентом
@app.route('/content')
@login_required
def content():
    conn = get_db_connection()
    content_items = conn.execute('SELECT * FROM content ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('content.html', content_items=content_items)

@app.route('/content/add', methods=['GET', 'POST'])
@login_required
def add_content():
    if request.method == 'POST':
        content_type = request.form['content_type']
        title = request.form['title']
        description = request.form['description']
        link = request.form['link']
        
        # Проверка заполнения обязательных полей
        if not title:
            flash('Заголовок обязателен для заполнения!', 'danger')
            return render_template('content_form.html', title='Добавление контента')
        
        conn = get_db_connection()
        conn.execute('INSERT INTO content (content_type, title, description, link) VALUES (?, ?, ?, ?)',
                     (content_type, title, description, link))
        conn.commit()
        conn.close()
        
        flash('Контент успешно добавлен!', 'success')
        return redirect(url_for('content'))
    
    return render_template('content_form.html', title='Добавление контента')

@app.route('/content/edit/<int:content_id>', methods=['GET', 'POST'])
@login_required
def edit_content(content_id):
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
        
        # Проверка заполнения обязательных полей
        if not title:
            flash('Заголовок обязателен для заполнения!', 'danger')
            return render_template('content_form.html', title='Редактирование контента', content=content)
        
        conn = get_db_connection()
        conn.execute('UPDATE content SET content_type = ?, title = ?, description = ?, link = ? WHERE content_id = ?',
                     (content_type, title, description, link, content_id))
        conn.commit()
        conn.close()
        
        flash('Контент успешно обновлен!', 'success')
        return redirect(url_for('content'))
    
    return render_template('content_form.html', title='Редактирование контента', content=content)

@app.route('/content/delete/<int:content_id>', methods=['POST'])
@login_required
def delete_content(content_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM content WHERE content_id = ?', (content_id,))
    conn.commit()
    conn.close()
    
    flash('Контент успешно удален!', 'success')
    return redirect(url_for('content'))

# Управление пользователями
@app.route('/users')
@login_required
def users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY registration_date DESC').fetchall()
    conn.close()
    return render_template('users.html', users=users)

# Отправка сообщений
@app.route('/send-message', methods=['GET', 'POST'])
@login_required
def send_message():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY first_name, last_name').fetchall()
    conn.close()
    
    if request.method == 'POST':
        message_text = request.form['message_text']
        send_to_all = 'send_to_all' in request.form
        
        if not message_text:
            flash('Текст сообщения обязателен!', 'danger')
            return render_template('send_message.html', users=users)
        
        # Получаем список пользователей для отправки
        if send_to_all:
            conn = get_db_connection()
            recipients = conn.execute('SELECT user_id FROM users').fetchall()
            conn.close()
        else:
            user_ids = request.form.getlist('user_ids')
            if not user_ids:
                flash('Выберите хотя бы одного пользователя для отправки!', 'danger')
                return render_template('send_message.html', users=users)
            
            conn = get_db_connection()
            placeholders = ','.join(['?'] * len(user_ids))
            recipients = conn.execute(f'SELECT user_id FROM users WHERE user_id IN ({placeholders})', user_ids).fetchall()
            conn.close()
        
        # Здесь должен быть код для отправки сообщения через бота
        # Но для демонстрации просто покажем успех
        
        recipient_count = len(recipients)
        flash(f'Сообщение успешно отправлено {recipient_count} пользователям!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('send_message.html', users=users)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)

# В конце файла admin_panel.py добавьте:
import os

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)