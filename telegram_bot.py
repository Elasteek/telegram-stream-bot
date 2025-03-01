"""
Telegram бот для управления полезными материалами и образовательными последовательностями
"""
import requests
import os
import logging
from datetime import datetime, timedelta
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, Filters, CallbackContext
from dotenv import load_dotenv
import threading
import time

def send_message_to_admin(user_id, first_name, last_name, username, text):
    admin_panel_url = "https://rough-rora-flatloops-eaeed163.koyeb.app/api/bot/receive_message"
    
    data = {
        "user_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "text": text
    }
    
    logger.info(f"Отправка сообщения в админ-панель URL: {admin_panel_url}")
    logger.info(f"Данные для отправки: {data}")
    
    try:
        response = requests.post(admin_panel_url, json=data)
        logger.info(f"Статус код ответа: {response.status_code}")
        logger.info(f"Тело ответа: {response.text}")
        
        success = response.status_code == 200
        logger.info(f"Сообщение отправлено в админ-панель: {success}")
        return success
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в админ-панель: {e}")
        return False

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot_log.txt'  # Записываем логи в файл для анализа
)
logger = logging.getLogger(__name__)

# Состояния для диалога регистрации
CONTACT = 0

# Подключение к базе данных
def get_db_connection():
    conn = sqlite3.connect('stream_bot.db')
    conn.row_factory = sqlite3.Row
    return conn

# Функция для отправки сообщения пользователю
def send_message_to_user(bot, user_id, text, reply_markup=None):
    try:
        bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
        return False

# Обработчики команд
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    
    # Проверяем, зарегистрирован ли пользователь
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()
    conn.close()
    
    if existing_user:
        update.message.reply_text(
            f"Привет, {user.first_name}! Рады видеть вас снова!",
            reply_markup=ReplyKeyboardRemove()
        )
        # Вместо мгновенной отправки планируем отправку приглашения через 2 минуты
        context.job_queue.run_once(
            send_welcome_invite, 
            120, 
            context={'user_id': user_id}
        )
        logger.info(f"Запланирована отправка приглашения в канал через 2 минуты для пользователя {user_id}")
        
        show_main_menu(update, context)
    else:
        update.message.reply_text(
            f"Привет, {user.first_name}! Добро пожаловать! "
            f"Для завершения регистрации, пожалуйста, поделитесь вашим контактом."
        )
        
        # Создаем кнопку для отправки контакта
        keyboard = [
            [KeyboardButton("Поделиться контактом", request_contact=True)]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text("Нажмите кнопку ниже:", reply_markup=reply_markup)
        
        return CONTACT

def send_welcome_invite(context: CallbackContext):
    """Отправляет приветственное сообщение с приглашением в канал через 2 минуты"""
    job = context.job
    user_id = job.context['user_id']
    
    logger.info(f"Отправка отложенного приглашения в канал для пользователя {user_id}")
    
    try:
        context.bot.send_message(
            chat_id=user_id,
            text="Присоединяйтесь к нашему закрытому каналу Flatloops School: @flatloops_school"
        )
        logger.info(f"Отложенное приглашение успешно отправлено пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке отложенного приглашения: {e}")

def process_contact(update: Update, context: CallbackContext):
    user = update.effective_user
    contact = update.message.contact
    phone = contact.phone_number
    
    # Сохраняем пользователя в базу данных
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, phone) VALUES (?, ?, ?, ?, ?)",
        (user.id, user.username, user.first_name, user.last_name, phone)
    )
    conn.commit()
    conn.close()
    
    # Отправляем новое приветственное сообщение
    update.message.reply_text(
        "Flatloops School: Твой путь в электронной музыке 🎧🚀\n\n"
        "Приглашаю тебя в Flatloops School — пространство для создания профессиональной электронной музыки.\n\n"
        "Что тебя ждет:\n"
        "* Экспертные статьи о музыкальном продакшене\n"
        "* Живое общение с профессионалами\n"
        "* Мастер-классы от признанных продюсеров\n"
        "* Эксклюзивные видеоуроки и разборы треков\n"
        "* Персональная обратная связь от экспертов\n"
        "* Нетворкинг с музыкантами со всего мира\n\n"
        "Твой уровень не важен — важно желание творить и развиваться.\n"
        "Готов создавать музыку мечты? 👉 Присоединяйся: https://t.me/+r4YENOpRDldjNmEy 🎚️🎶",
        reply_markup=ReplyKeyboardRemove()  # Убираем клавиатуру запроса контакта
    )
    
    # Показываем главное меню
    show_main_menu(update, context)
    
    # Планируем отправку приглашения через 2 минуты (120 секунд)
    context.job_queue.run_once(
        send_welcome_invite, 
        120, 
        context={'user_id': user.id}
    )
    
    # Планируем уведомления для нового пользователя
    schedule_user_notifications(user.id)
    
    return ConversationHandler.END

def show_main_menu(update: Update, context: CallbackContext):
    # Вертикальные кнопки, сохраняя оригинальные названия, кроме "Стримы"
    keyboard = [
        [InlineKeyboardButton("📚 Полезные материалы", callback_data="useful_content")],
        [InlineKeyboardButton("🎓 Бесплатные мини курсы", callback_data="educational_paths")],
        [InlineKeyboardButton("💼 Наши курсы", callback_data="our_courses")],
        [InlineKeyboardButton("🎬 Стримы", callback_data="upcoming_streams")],
        [InlineKeyboardButton("✍️ Напиши нам", callback_data="feedback")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Проверяем, откуда был вызван метод
    if update.callback_query:
        update.callback_query.edit_message_text(
            "Выберите раздел:", reply_markup=reply_markup
        )
    else:
        update.message.reply_text(
            "Выберите раздел:", reply_markup=reply_markup
        )

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    if query.data == "upcoming_streams":
        show_upcoming_streams(update, context)
    elif query.data == "useful_content":
        show_useful_content(update, context)
    elif query.data == "educational_paths": 
        show_educational_paths(update, context)
    elif query.data == "our_courses":
        show_courses(update, context)
    elif query.data == "feedback":
        request_feedback(update, context)
    elif query.data == "main_menu":
        show_main_menu(update, context)
    elif query.data.startswith("select_path_"):
        # Обработка выбора образовательной цепочки
        path_id = int(query.data.split("_")[2])
        subscribe_to_path(update, context, path_id)
    elif query.data.startswith("view_current_"):
        # Обработка запроса на просмотр текущего материала курса
        path_id = int(query.data.split("_")[2])
        show_current_material(update, context, path_id)
    else:
        # Обработка других кнопок
        pass

# Функции для показа информации
def show_upcoming_streams(update: Update, context: CallbackContext):
    query = update.callback_query
    
    conn = get_db_connection()
    upcoming_streams = conn.execute("""
    SELECT stream_id, title, description, stream_date, is_closed
    FROM streams
    WHERE stream_date > datetime('now')
    ORDER BY stream_date
    LIMIT 5
    """).fetchall()
    conn.close()
    
    if not upcoming_streams:
        query.edit_message_text(
            "В настоящее время нет запланированных стримов. "
            "Мы сообщим вам, когда появятся новые стримы!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="main_menu")]])
        )
        return
    
    text = "📺 Ближайшие стримы:\n\n"
    for stream in upcoming_streams:
        # Форматируем дату из строки
        try:
            stream_date = datetime.fromisoformat(stream['stream_date'].replace('Z', '+00:00'))
            formatted_date = stream_date.strftime('%d.%m.%Y %H:%M')
        except:
            formatted_date = stream['stream_date']  # Если не удалось преобразовать, оставляем как есть
        
        text += f"🎬 {stream['title']}\n"
        text += f"📝 {stream['description']}\n"
        text += f"📅 {formatted_date}\n"
        if stream['is_closed']:
            text += "🔒 Закрытый стрим\n"
        text += "\n"
    
    keyboard = [[InlineKeyboardButton("Назад", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(text=text, reply_markup=reply_markup)

def show_useful_content(update: Update, context: CallbackContext):
    query = update.callback_query
    
    conn = get_db_connection()
    # Показываем только нескрытый контент
    content_items = conn.execute("""
    SELECT content_id, content_type, title, description, link, image_url, file_url
    FROM content
    WHERE is_hidden = 0 OR is_hidden IS NULL
    ORDER BY created_at DESC
    LIMIT 5
    """).fetchall()
    conn.close()
    
    if not content_items:
        query.edit_message_text(
            "В настоящее время нет доступных материалов. "
            "Мы добавим новые материалы в ближайшее время!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="main_menu")]])
        )
        return
    
    text = "📚 Полезные материалы:\n\n"
    for item in content_items:
        text += f"📌 {item['title']}\n"
        text += f"📝 {item['description']}\n"
        if item['link']:
            text += f"🔗 {item['link']}\n"
        if item['image_url'] or item['file_url']:
            text += "📎 Доступны дополнительные материалы\n"
        text += "\n"
    
    keyboard = [[InlineKeyboardButton("Назад", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(text=text, reply_markup=reply_markup)

def show_courses(update: Update, context: CallbackContext):
    query = update.callback_query
    
    conn = get_db_connection()
    # Проверяем, существует ли таблица courses
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='courses'")
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        # Создаем таблицу курсов, если она еще не существует
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
        conn.commit()
        
        # Добавляем начальные курсы в базу данных
        default_courses = [
            ("Для начинающих - Основы музыкального продюсирования", 
             "Базовый курс для всех, кто хочет начать создавать электронную музыку", 
             "https://www.flatloops.ru/osnovy_muzykalnogo_prodyusirovaniya", 1),
            ("Продвинутый курс - Создание техно-трека: от идеи до работы с лейблами", 
             "Для тех, кто хочет углубить свои знания и научиться работать с лейблами", 
             "https://www.flatloops.ru/education/online-group/sozdanie-tehno-treka-ot-idei-do-masteringa", 2),
            ("Продвинутый курс - Техника live выступлений: играй вживую свои треки", 
             "Научитесь выступать вживую и представлять свою музыку публике", 
             "https://www.flatloops.ru/education/online-group/tehnika-live-vystuplenij", 3)
        ]
        
        cursor.executemany('''
            INSERT INTO courses (title, description, link, order_num) 
            VALUES (?, ?, ?, ?)
        ''', default_courses)
        conn.commit()
    
    # Получаем активные курсы из базы данных, отсортированные по order_num
    courses = conn.execute('''
        SELECT * FROM courses 
        WHERE is_active = 1 
        ORDER BY order_num
    ''').fetchall()
    conn.close()
    
    if not courses:
        query.edit_message_text(
            "В настоящее время курсы не доступны. Пожалуйста, проверьте позже.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="main_menu")]])
        )
        return
    
    text = "💼 Наши курсы:\n\n"
    
    for i, course in enumerate(courses, 1):
        # Добавляем emoji в зависимости от номера курса
        if i == 1:
            emoji = "1️⃣"
        elif i == 2:
            emoji = "2️⃣"
        elif i == 3:
            emoji = "3️⃣"
        elif i == 4:
            emoji = "4️⃣"
        elif i == 5:
            emoji = "5️⃣"
        else:
            emoji = "🔹"
        
        text += f"{emoji} {course['title']}\n"
        if course['description']:
            text += f"{course['description']}\n"
        text += f"👉 {course['link']}\n\n"
    
    keyboard = [[InlineKeyboardButton("Назад", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(text=text, reply_markup=reply_markup)

def request_feedback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    
    # Переименовываем функцию из "Обратная связь" в "Напиши нам"
    text = "✍️ Напишите нам сообщение, и наша команда ответит вам в ближайшее время.\n\n"
    text += "Что бы вы хотели узнать или сообщить?"
    
    context.user_data['waiting_for_feedback'] = True
    
    keyboard = [[InlineKeyboardButton("Назад", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(text=text, reply_markup=reply_markup)

# Функция для показа текущего материала курса
def show_current_material(update: Update, context: CallbackContext, path_id):
    query = update.callback_query
    user_id = query.from_user.id
    
    conn = get_db_connection()
    
    # Получаем информацию о цепочке
    sequence = conn.execute("SELECT * FROM content_sequences WHERE sequence_id = ?", (path_id,)).fetchone()
    
    if not sequence:
        conn.close()
        query.edit_message_text("Выбранный курс не найден. Пожалуйста, выберите другой курс.",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="educational_paths")]]))
        return
    
    # Получаем текущий день пользователя в этой последовательности
    user_sequence = conn.execute("""
        SELECT * FROM user_sequences 
        WHERE user_id = ? AND sequence_id = ? AND is_active = 1
    """, (user_id, path_id)).fetchone()
    
    if not user_sequence or user_sequence['current_day'] == 0:
        conn.close()
        query.edit_message_text("У вас нет активного прогресса по этому курсу.",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="educational_paths")]]))
        return
    
    current_day = user_sequence['current_day']
    
    # Получаем текущий материал
    current_content = conn.execute("""
        SELECT c.* 
        FROM sequence_items si
        JOIN content c ON si.content_id = c.content_id
        WHERE si.sequence_id = ? AND si.day_number = ?
    """, (path_id, current_day)).fetchone()
    
    if not current_content:
        conn.close()
        query.edit_message_text("Материал не найден. Пожалуйста, обратитесь в поддержку.",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="educational_paths")]]))
        return
    
    # Формируем текст сообщения
    message_text = f"🎓 Ваш текущий материал курса \"{sequence['title']}\" (день {current_day} из {sequence['days_count']}):\n\n"
    message_text += f"📌 {current_content['title']}\n"
    message_text += f"📝 {current_content['description']}\n"
    
    if current_content['link']:
        message_text += f"🔗 {current_content['link']}\n"
    
    # Если это последний день курса, добавляем промокод
    if current_day == sequence['days_count']:
        message_text += "\n🎉 Поздравляем с завершением мини-курса! 🎉\n"
        message_text += "Вы успешно прошли все этапы обучения.\n\n"
        message_text += "🎁 Специально для вас мы подготовили ПРОМОКОД на скидку 20% на полный курс:\n"
        message_text += "PROMO_" + sequence['title'].replace(" ", "_").upper() + "\n\n"
        message_text += "Используйте его при оформлении нашего полного курса на сайте:\n"
        message_text += "https://www.flatloops.ru/education\n\n"
        message_text += "Промокод действителен в течение 7 дней. Не упустите возможность!"
    
    conn.close()
    
    # Отправляем сообщение с материалом и кнопкой возврата
    query.edit_message_text(text=message_text, 
                           reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="educational_paths")]]))

# Новая функция для показа доступных образовательных цепочек
def show_educational_paths(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    
    conn = get_db_connection()
    
    # Получаем доступные образовательные цепочки
    paths = conn.execute("""
    SELECT cs.sequence_id, cs.title, cs.description, cs.days_count 
    FROM content_sequences cs
    WHERE cs.sequence_id NOT IN (
        SELECT sequence_id FROM user_sequences WHERE user_id = ?
    )
    ORDER BY cs.created_at DESC
    """, (user_id,)).fetchall()
    
    # Получаем активные подписки пользователя
    active_paths = conn.execute("""
    SELECT cs.sequence_id, cs.title, us.current_day, cs.days_count
    FROM user_sequences us
    JOIN content_sequences cs ON us.sequence_id = cs.sequence_id
    WHERE us.user_id = ? AND us.is_active = 1
    ORDER BY us.start_date DESC
    """, (user_id,)).fetchall()
    
    conn.close()
    
    text = "🎓 Бесплатные мини курсы\n\n"
    
    # Показываем активные подписки
    if active_paths:
        text += "Ваши активные курсы:\n\n"
        for path in active_paths:
            progress = round((path['current_day'] / path['days_count']) * 100)
            text += f"📝 {path['title']}\n"
            text += f"📊 Прогресс: {path['current_day']}/{path['days_count']} ({progress}%)\n\n"
    
    # Показываем доступные цепочки
    if paths:
        text += "Доступные бесплатные курсы:\n\n"
        for path in paths:
            text += f"🔹 {path['title']}\n"
            text += f"📝 {path['description']}\n"
            text += f"⏱ Продолжительность: {path['days_count']} дней\n\n"
    else:
        if not active_paths:  # Если нет ни активных, ни доступных цепочек
            text += "В настоящее время нет доступных образовательных курсов.\n"
    
    # Добавляем кнопки для просмотра текущих материалов - вертикально
    keyboard = []
    for path in active_paths:
        keyboard.append([InlineKeyboardButton(f"📖 Просмотреть: {path['title']}", 
                                           callback_data=f"view_current_{path['sequence_id']}")])
    
    # Добавляем кнопки для выбора новых курсов - вертикально
    for path in paths:
        keyboard.append([InlineKeyboardButton(f"▶️ Начать: {path['title']}", 
                                           callback_data=f"select_path_{path['sequence_id']}")])
    
    keyboard.append([InlineKeyboardButton("Назад", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(text=text, reply_markup=reply_markup)

# Функция для подписки на образовательную цепочку
def subscribe_to_path(update: Update, context: CallbackContext, path_id):
    query = update.callback_query
    user_id = query.from_user.id
    
    conn = get_db_connection()
    
    # Проверяем, существует ли цепочка
    path = conn.execute("SELECT * FROM content_sequences WHERE sequence_id = ?", (path_id,)).fetchone()
    
    if not path:
        conn.close()
        query.edit_message_text("Выбранный курс не найден. Пожалуйста, выберите другой курс.")
        return
    
    # Проверяем, не подписан ли уже пользователь
    existing = conn.execute("""
        SELECT COUNT(*) FROM user_sequences 
        WHERE user_id = ? AND sequence_id = ?
    """, (user_id, path_id)).fetchone()[0]
    
    if existing > 0:
        # Обновляем существующую подписку
        conn.execute("""
            UPDATE user_sequences
            SET is_active = 1, current_day = 0, start_date = datetime('now')
            WHERE user_id = ? AND sequence_id = ?
        """, (user_id, path_id))
    else:
        # Создаем новую подписку
        conn.execute("""
            INSERT INTO user_sequences 
            (user_id, sequence_id, current_day, start_date, is_active)
            VALUES (?, ?, 0, datetime('now'), 1)
        """, (user_id, path_id))
    
    conn.commit()
    
    # Получаем первый день контента
    first_day_content = conn.execute("""
    SELECT c.* 
    FROM sequence_items si
    JOIN content c ON si.content_id = c.content_id
    WHERE si.sequence_id = ? AND si.day_number = 1
    """, (path_id,)).fetchone()
    
    # Отправляем первый материал прямо сейчас
    if first_day_content:
        message_text = f"🎓 Ваш первый материал курса \"{path['title']}\":\n\n"
        message_text += f"📌 {first_day_content['title']}\n"
        message_text += f"📝 {first_day_content['description']}\n"
        
        if first_day_content['link']:
            message_text += f"🔗 {first_day_content['link']}\n"
        
        # Обновляем прогресс пользователя
        conn.execute("""
        UPDATE user_sequences
        SET current_day = 1
        WHERE user_id = ? AND sequence_id = ?
        """, (user_id, path_id))
        conn.commit()
    else:
        message_text = f"🎓 Вы успешно подписались на курс \"{path['title']}\"!\n\n"
        message_text += "Первый материал будет отправлен вам завтра."
    
    conn.close()
    
    # Отвечаем пользователю
    keyboard = [
        [InlineKeyboardButton("Перейти к курсам", callback_data="educational_paths")],
        [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(text=message_text, reply_markup=reply_markup)

# Словарь для отслеживания последних сообщений пользователей
last_message_times = {}

def process_message(update: Update, context: CallbackContext):
    """Обрабатывает все текстовые сообщения от пользователя"""
    user = update.effective_user
    user_id = user.id
    text = update.message.text
    
    # Проверяем, зарегистрирован ли пользователь
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()
    conn.close()
    
    # Если пользователь новый, предлагаем ему запустить бота
    if not existing_user:
        keyboard = [[KeyboardButton("/start")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text(
            f"Привет, {user.first_name}! Чтобы начать работу с ботом, нажмите кнопку Старт ниже:",
            reply_markup=reply_markup
        )
        return
    
    # Отправляем сообщение в админ-панель в любом случае
    send_message_to_admin(
        user.id,
        user.first_name,
        user.last_name if user.last_name else "",
        user.username if user.username else "",
        text
    )
    
    # Проверяем, ожидается ли обратная связь от пользователя
    if context.user_data.get('waiting_for_feedback'):
        # Сбрасываем флаг ожидания обратной связи
        del context.user_data['waiting_for_feedback']
        
        update.message.reply_text(
            "Спасибо за ваше сообщение! Наша команда скоро свяжется с вами."
        )
        
        # Добавляем текущее время в словарь последних сообщений
        last_message_times[user_id] = datetime.now()
        
        # Не показываем главное меню после фидбека - так выглядит чище
        return
    else:
        # Проверяем, когда пользователь последний раз получал уведомление
        current_time = datetime.now()
        last_time = last_message_times.get(user_id)
        
        # Если прошло менее 24 часов, не отправляем "Спасибо за сообщение"
        if last_time and (current_time - last_time).total_seconds() < 86400:  # 86400 секунд = 24 часа
            pass
        else:
            update.message.reply_text(
                "Спасибо за ваше сообщение! Наша команда скоро свяжется с вами."
            )
            last_message_times[user_id] = current_time
    
    # Показываем главное меню только для новых пользователей или если прошло более 7 дней
    if not last_time or (current_time - last_time).days > 7:
        show_main_menu(update, context)

# Функции для уведомлений
def schedule_user_notifications(user_id):
    """Планирует уведомления для пользователя на основе контента и образовательных последовательностей"""
    
    conn = get_db_connection()
    
    # Создаем таблицу уведомлений, если она не существует
    conn.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        stream_id INTEGER,
        content_id INTEGER,
        notification_type TEXT,
        sent INTEGER DEFAULT 0,
        scheduled_time TEXT
    )
    """)
    
    # Получаем все предстоящие стримы
    upcoming_streams = conn.execute("""
    SELECT stream_id, title, stream_date, is_closed, access_link
    FROM streams
    WHERE stream_date > datetime('now')
    ORDER BY stream_date
    """).fetchall()
    
    # Удаляем старые запланированные уведомления для этого пользователя
    conn.execute("DELETE FROM notifications WHERE user_id = ? AND sent = 0", (user_id,))
    
    for stream in upcoming_streams:
        stream_id = stream['stream_id']
        stream_date_str = stream['stream_date']
        
        # Преобразуем строку в datetime
        try:
            stream_date = datetime.fromisoformat(stream_date_str.replace('Z', '+00:00'))
        except:
            # Если не в ISO формате, пробуем другие форматы
            try:
                stream_date = datetime.strptime(stream_date_str, '%Y-%m-%d %H:%M:%S')
            except:
                logger.error(f"Не удалось распарсить дату для стрима {stream_id}: {stream_date_str}")
                continue
        
        now = datetime.now()
        
        # Проверяем, что стрим в будущем
        if stream_date <= now:
            continue
        
        # Расчет дней до стрима
        days_until_stream = (stream_date - now).days
        
        # Планируем уведомления за день, за два и т.д. до стрима
        # Уменьшаем количество уведомлений о стримах, т.к. они теперь не в приоритете
        if days_until_stream > 0:
            notification_date = stream_date - timedelta(days=1)
            
            # Добавляем уведомление в базу
            conn.execute(
                """
                INSERT INTO notifications 
                (user_id, stream_id, notification_type, scheduled_time) 
                VALUES (?, ?, ?, ?)
                """,
                (user_id, stream_id, 'reminder', notification_date.strftime('%Y-%m-%d %H:%M:%S'))
            )
        
        # Напоминание в день стрима (утром)
        morning_time = stream_date.replace(hour=9, minute=0, second=0)
        if morning_time > now:
            conn.execute(
                """
                INSERT INTO notifications 
                (user_id, stream_id, notification_type, scheduled_time) 
                VALUES (?, ?, ?, ?)
                """,
                (user_id, stream_id, 'day_of_stream', morning_time.strftime('%Y-%m-%d %H:%M:%S'))
            )
    
    # Планируем образовательные последовательности для пользователя
    # Получаем активные последовательности пользователя
    user_sequences = conn.execute("""
    SELECT us.*, cs.days_count
    FROM user_sequences us
    JOIN content_sequences cs ON us.sequence_id = cs.sequence_id
    WHERE us.user_id = ? AND us.is_active = 1
    """, (user_id,)).fetchall()
    
    for sequence in user_sequences:
        sequence_id = sequence['sequence_id']
        current_day = sequence['current_day']
        days_count = sequence['days_count']
        
        # Если пользователь еще не прошел всю последовательность
        if current_day < days_count:
            # Получаем контент для следующего дня
            next_day = current_day + 1
            content_item = conn.execute("""
            SELECT si.content_id
            FROM sequence_items si
            WHERE si.sequence_id = ? AND si.day_number = ?
            """, (sequence_id, next_day)).fetchone()
            
            if content_item:
                content_id = content_item['content_id']
                
                # Планируем отправку на следующий день
                next_notification_date = datetime.now() + timedelta(days=1)
                next_notification_time = next_notification_date.replace(hour=10, minute=0, second=0)
                
                conn.execute("""
                INSERT INTO notifications 
                (user_id, content_id, notification_type, scheduled_time) 
                VALUES (?, ?, ?, ?)
                """, (user_id, content_id, 'sequence', next_notification_time.strftime('%Y-%m-%d %H:%M:%S')))
    
    # Планируем бонусные уведомления (контент)
    content_count = conn.execute("SELECT COUNT(*) FROM content WHERE is_hidden = 0 OR is_hidden IS NULL").fetchone()[0]
    
    if content_count > 0:
        # Определяем, сколько бонусных уведомлений планировать
        # Увеличиваем количество бонусных уведомлений, т.к. контент теперь в приоритете
        bonus_count = min(content_count, 15)  # До 15 бонусных уведомлений
        
        for i in range(bonus_count):
            # Уведомление каждые 1-2 дня
            bonus_date = datetime.now() + timedelta(days=i*1.5 + 1)
            
            conn.execute("""
            INSERT INTO notifications 
            (user_id, content_id, notification_type, scheduled_time) 
            VALUES (?, NULL, ?, ?)
            """, (user_id, 'bonus', bonus_date.strftime('%Y-%m-%d %H:%M:%S')))
    
    conn.commit()
    conn.close()

def send_pending_notifications(bot):
    """Отправляет все запланированные уведомления, время которых уже наступило"""
    
    logger.info("Проверка и отправка уведомлений...")
    
    conn = get_db_connection()
    
    # Получаем все запланированные уведомления, которые нужно отправить
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    notifications = conn.execute("""
    SELECT n.notification_id, n.user_id, n.stream_id, n.content_id, n.notification_type,
           s.title as stream_title, s.description as stream_desc, s.stream_date, s.is_closed, s.access_link,
           c.title as content_title, c.description as content_desc, c.link as content_link, 
           c.image_url, c.file_url
    FROM notifications n
    LEFT JOIN streams s ON n.stream_id = s.stream_id
    LEFT JOIN content c ON n.content_id = c.content_id
    WHERE n.sent = 0 AND n.scheduled_time <= ?
    """, (now,)).fetchall()
    
    logger.info(f"Найдено {len(notifications)} уведомлений для отправки")
    
    for notification in notifications:
        notification_id = notification['notification_id']
        user_id = notification['user_id']
        notification_type = notification['notification_type']
        
        # Готовим текст сообщения в зависимости от типа уведомления
        message_text = ""
        
        if notification_type == 'reminder':
            message_text = f"🔔 Напоминание о предстоящем стриме!\n\n"
            message_text += f"📺 {notification['stream_title']}\n"
            message_text += f"📝 {notification['stream_desc']}\n"
                
            # Форматируем дату
            try:
                stream_date = datetime.fromisoformat(notification['stream_date'].replace('Z', '+00:00'))
                days_until = (stream_date - datetime.now()).days
                message_text += f"⏳ До стрима осталось: {days_until} дней\n"
                message_text += f"📅 Дата: {stream_date.strftime('%d.%m.%Y %H:%M')}\n"
            except:
                message_text += f"📅 Дата: {notification['stream_date']}\n"
        
        elif notification_type == 'day_of_stream':
            message_text = f"🎬 Сегодня состоится стрим!\n\n"
            message_text += f"📺 {notification['stream_title']}\n"
            message_text += f"📝 {notification['stream_desc']}\n"
            
            # Форматируем время
            try:
                stream_date = datetime.fromisoformat(notification['stream_date'].replace('Z', '+00:00'))
                message_text += f"🕒 Начало в: {stream_date.strftime('%H:%M')}\n"
            except:
                pass
        
        elif notification_type == 'sequence':
            # Получаем информацию о цепочке
            sequence_info = conn.execute("""
            SELECT cs.title, si.day_number, cs.days_count
            FROM sequence_items si
            JOIN content_sequences cs ON si.sequence_id = cs.sequence_id
            WHERE si.content_id = ?
            """, (notification['content_id'],)).fetchone()
            
            if sequence_info:
                message_text = f"🎓 День {sequence_info['day_number']} из {sequence_info['days_count']}: {sequence_info['title']}\n\n"
                message_text += f"📌 {notification['content_title']}\n"
                message_text += f"📝 {notification['content_desc']}\n"
                if notification['content_link']:
                    message_text += f"🔗 {notification['content_link']}\n"
                
                # Если это последний день курса, добавляем промокод или предложение
                if sequence_info['day_number'] == sequence_info['days_count']:
                    message_text += "\n🎉 Поздравляем с завершением мини-курса! 🎉\n"
                    message_text += "Вы успешно прошли все этапы обучения.\n\n"
                    message_text += "🎁 Специально для вас мы подготовили ПРОМОКОД на скидку 20% на полный курс:\n"
                    message_text += "PROMO_" + sequence_info['title'].replace(" ", "_").upper() + "\n\n"
                    message_text += "Используйте его при оформлении нашего полного курса на сайте:\n"
                    message_text += "https://www.flatloops.ru/education\n\n"
                    message_text += "Промокод действителен в течение 7 дней. Не упустите возможность!"
                    
                # Обновляем текущий день в последовательности для пользователя
                conn.execute("""
                UPDATE user_sequences
                SET current_day = ?
                WHERE user_id = ? AND sequence_id = (
                    SELECT si.sequence_id FROM sequence_items si WHERE si.content_id = ?
                )
                """, (sequence_info['day_number'], user_id, notification['content_id']))
            else:
                message_text = f"📚 Полезный материал для вас!\n\n"
                message_text += f"📌 {notification['content_title']}\n"
                message_text += f"📝 {notification['content_desc']}\n"
                if notification['content_link']:
                    message_text += f"🔗 {notification['content_link']}\n"
        
        elif notification_type == 'bonus':
            # Получаем случайный контент, исключая скрытый
            content = conn.execute("""
            SELECT title, description, link, image_url, file_url
            FROM content
            WHERE is_hidden = 0 OR is_hidden IS NULL
            ORDER BY RANDOM()
            LIMIT 1
            """).fetchone()
            
            if content:
                message_text = f"🎁 Полезный материал для вас!\n\n"
                message_text += f"📌 {content['title']}\n"
                message_text += f"📝 {content['description']}\n"
                if content['link']:
                    message_text += f"🔗 {content['link']}\n"
                if content['image_url'] or content['file_url']:
                    message_text += "📎 Доступны дополнительные материалы\n"
            else:
                # Если контента нет, не отправляем уведомление
                conn.execute("UPDATE notifications SET sent = 1 WHERE notification_id = ?", (notification_id,))
                continue
        
        # Отправляем уведомление
        success = send_message_to_user(bot, user_id, message_text)
        
        # Отмечаем уведомление как отправленное
        if success:
            conn.execute("UPDATE notifications SET sent = 1 WHERE notification_id = ?", (notification_id,))
            logger.info(f"Уведомление {notification_id} отправлено пользователю {user_id}")
        else:
            logger.error(f"Не удалось отправить уведомление {notification_id} пользователю {user_id}")
    
    conn.commit()
    conn.close()

def fetch_and_send_admin_messages(bot):
    """Получает сообщения от админ-панели и отправляет их пользователям"""
    
    logger.info("Проверка наличия новых сообщений от админ-панели...")
    
    try:
        # URL админ-панели для получения сообщений
        url = "https://rough-rora-flatloops-eaeed163.koyeb.app/api/bot/get_messages"
        
        # Запрашиваем сообщения для отправки
        response = requests.get(url)
        
        if response.status_code != 200:
            logger.error(f"Ошибка при получении сообщений: HTTP {response.status_code}")
            return
        
        messages = response.json()
        logger.info(f"Получено {len(messages)} сообщений для отправки")
        
        for message in messages:
            message_id = message.get('id')
            user_id = message.get('user_id')
            text = message.get('text')
            
            if not message_id or not user_id or not text:
                logger.error(f"Некорректное сообщение: {message}")
                continue
            
            # Отправляем сообщение пользователю
            success = send_message_to_user(bot, user_id, text)
            
            if success:
                # Отмечаем сообщение как отправленное
                mark_url = f"https://rough-rora-flatloops-eaeed163.koyeb.app/api/bot/mark_sent/{message_id}"
                mark_response = requests.post(mark_url)
                
                if mark_response.status_code == 200:
                    logger.info(f"Сообщение {message_id} отмечено как отправленное")
                else:
                    logger.error(f"Ошибка при отметке сообщения {message_id}: HTTP {mark_response.status_code}")
            else:
                logger.error(f"Не удалось отправить сообщение {message_id} пользователю {user_id}")
    
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщений от админ-панели: {e}")

def notifications_scheduler(updater):
    """Планировщик для регулярной проверки и отправки уведомлений"""
    bot = updater.bot
    
    while True:
        try:
            # Отправка уведомлений
            send_pending_notifications(bot)
            
            # Проверка сообщений от админ-панели
            fetch_and_send_admin_messages(bot)
            
            # Проверка наличия новых стримов для планирования уведомлений
            conn = get_db_connection()
            users = conn.execute("SELECT user_id FROM users").fetchall()
            conn.close()
            
            for user in users:
                schedule_user_notifications(user['user_id'])
                
        except Exception as e:
            logger.error(f"Ошибка в планировщике: {e}")
        
        # Ждем некоторое время перед следующей проверкой
        time.sleep(60)  # Проверка каждую минуту

def run_notifications_scheduler(updater):
    """Запускает планировщик уведомлений в отдельном потоке"""
    thread = threading.Thread(target=notifications_scheduler, args=(updater,), daemon=True)
    thread.start()

def main():
    # Инициализация базы данных
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Создаем необходимые таблицы, если они не существуют
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
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS content (
        content_id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        link TEXT,
        image_url TEXT,
        file_url TEXT,
        is_hidden INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS content_sequences (
        sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        days_count INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
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
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        stream_id INTEGER,
        content_id INTEGER,
        notification_type TEXT,
        sent INTEGER DEFAULT 0,
        scheduled_time TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
        feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        stream_id INTEGER,
        feedback_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Создаем таблицу для курсов, если она не существует
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
    
    # Добавляем индекс для быстрого поиска контента по статусу скрытия, если его нет
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_content_is_hidden ON content (is_hidden)
    ''')
    
    conn.commit()
    conn.close()
    
    # Настраиваем бота
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher
    
    # Добавляем обработчики команд
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CONTACT: [MessageHandler(Filters.contact, process_contact)]
        },
        fallbacks=[CommandHandler('cancel', lambda update, context: ConversationHandler.END)]
    )
    
    dispatcher.add_handler(conversation_handler)
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    
    # Обработчик текстовых сообщений
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, process_message))
    
    # Запускаем планировщик уведомлений в отдельном потоке
    run_notifications_scheduler(updater)
    
    # Запускаем бота
    updater.start_polling()
    
    logger.info("Бот запущен и готов к работе!")
    
    try:
        # Держим бота работающим до Ctrl+C
        updater.idle()
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки, завершение работы...")
    finally:
        logger.info("Бот остановлен")

if __name__ == '__main__':
    main()