import os
import logging
import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for, flash
from datetime import datetime
cat > admin_panel.py << 'EOF'
import os
import logging
import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for, flash
from datetime import datetime
cat > admin_panel.py << 'EOF'
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
    
    # Получаем статистику
    conn = get_db_connection()
    
    # Количество стримов
    cursor = conn.cursor()
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
        user_count=0,
        stream_count=stream_count, 
        content_count=content_count,
        streams=streams
    )

# Управление стримами
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

# Управление контентом
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
    logger.debug("Выход из системы")
    session.clear()
    flash('Вы вышли из системы!', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Запуск приложения на порту {port}")
    app.run(host='0.0.0.0', port=port)
