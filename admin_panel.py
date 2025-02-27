import os
import logging
from flask import Flask, render_template, request, session, redirect, url_for, jsonify

# Настройка логирования для отладки
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'debug_key_123'

# Начальная тестовая страница
@app.route('/')
def index():
    logger.debug("Запрос к корневому маршруту /")
    return "Приложение работает! <a href='/login'>Войти</a>"

# Простейшая страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    logger.debug(f"Запрос к /login, метод: {request.method}")
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        logger.debug(f"Попытка входа: username={username}, password={'*' * len(password) if password else 'None'}")
        
        # Простая проверка для тестирования
        if username == 'admin' and password == 'admin123':
            session['logged_in'] = True
            session['username'] = username
            logger.debug("Вход успешен, перенаправление на дашборд")
            return redirect(url_for('dashboard'))
        else:
            logger.debug("Ошибка входа - неверные учетные данные")
            return render_template('login.html', error="Неверное имя пользователя или пароль")
    
    logger.debug("Отображение формы входа")
    return render_template('login.html')

# Простой дашборд
@app.route('/dashboard')
def dashboard():
    logger.debug("Запрос к /dashboard")
    if not session.get('logged_in'):
        logger.debug("Перенаправление на страницу входа - пользователь не вошел в систему")
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# Выход из системы
@app.route('/logout')
def logout():
    logger.debug("Выход из системы")
    session.clear()
    return redirect(url_for('login'))

# Простой API для проверки работы
@app.route('/api/status')
def api_status():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Запуск приложения на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
