import os
from flask import Flask, request, render_template_string, redirect, url_for, flash
from telegram import Bot
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Настройки
BOT_TOKEN = "7503427825:AAH6bVm2IbO_mOZT_WuaoXbAcWvItQNWA4g"
SERVER_PORT = 5000

# Инициализация
bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Для работы flash-сообщений

# HTML-шаблон для главной страницы с формой отправки
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Отправка сообщений через бота</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { padding: 20px; }
        .container { max-width: 800px; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">Отправка сообщений пользователям через Telegram-бота</h1>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="card">
            <div class="card-body">
                <form method="post" action="/send">
                    <div class="mb-3">
                        <label for="user_id" class="form-label">ID пользователя в Telegram</label>
                        <input type="text" class="form-control" id="user_id" name="user_id" required>
                        <div class="form-text">Введите числовой ID пользователя, которому нужно отправить сообщение</div>
                    </div>
                    
                    <div class="mb-3">
                        <label for="message" class="form-label">Текст сообщения</label>
                        <textarea class="form-control" id="message" name="message" rows="5" required></textarea>
                    </div>
                    
                    <button type="submit" class="btn btn-primary">Отправить сообщение</button>
                </form>
            </div>
        </div>
        
        <div class="mt-4">
            <h3>История отправленных сообщений</h3>
            <div class="list-group">
                {% for msg in history %}
                <div class="list-group-item">
                    <div class="d-flex w-100 justify-content-between">
                        <h5 class="mb-1">Пользователь: {{ msg.user_id }}</h5>
                        <small>{{ msg.time }}</small>
                    </div>
                    <p class="mb-1">{{ msg.text }}</p>
                    <small class="text-muted">Статус: {{ msg.status }}</small>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# История отправленных сообщений
message_history = []

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, history=message_history)

@app.route('/send', methods=['POST'])
def send_message():
    user_id = request.form.get('user_id')
    message_text = request.form.get('message')
    
    if not user_id or not message_text:
        flash('Пожалуйста, заполните все поля', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Отправляем сообщение через бота
        bot.send_message(chat_id=user_id, text=message_text)
        
        # Добавляем в историю
        from datetime import datetime
        message_history.insert(0, {
            'user_id': user_id,
            'text': message_text,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'Отправлено'
        })
        
        # Ограничиваем историю 20 последними сообщениями
        if len(message_history) > 20:
            message_history.pop()
            
        flash('Сообщение успешно отправлено!', 'success')
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        flash(f'Ошибка при отправке сообщения: {e}', 'danger')
    
    return redirect(url_for('index'))

if __name__ == "__main__":
    try:
        # Проверяем подключение к боту
        bot_info = bot.get_me()
        logger.info(f"Бот успешно подключен: @{bot_info.username}")
        
        # Запускаем веб-сервер
        logger.info(f"Запуск веб-сервера на порту {SERVER_PORT}")
        app.run(host='0.0.0.0', port=SERVER_PORT, debug=True)
    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}")
