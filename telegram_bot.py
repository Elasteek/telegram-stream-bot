"""
Telegram бот для управления стримами и автоматизации оповещений
"""
import os
import logging
from datetime import datetime, timedelta
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes
from dotenv import load_dotenv
import asyncio
import threading
import time

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
async def send_message_to_user(bot, user_id, text, reply_markup=None):
    try:
        await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
        return False

# Обработчики команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Проверяем, зарегистрирован ли пользователь
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()
    conn.close()
    
    if existing_user:
        await update.message.reply_text(
            f"Привет, {user.first_name}! Рады видеть вас снова! "
            f"Вы уже зарегистрированы для получения уведомлений о стримах."
        )
        await show_main_menu(update, context)
    else:
        await update.message.reply_text(
            f"Привет, {user.first_name}! Добро пожаловать! "
            f"Для завершения регистрации, пожалуйста, поделитесь вашим контактом."
        )
        
        # Создаем кнопку для отправки контакта
        keyboard = [
            [KeyboardButton("Поделиться контактом", request_contact=True)]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("Нажмите кнопку ниже:", reply_markup=reply_markup)
        
        return CONTACT

async def process_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    # Отправляем благодарность
    await update.message.reply_text(
        f"Спасибо за регистрацию, {user.first_name}! "
        f"Теперь вы будете получать уведомления о наших стримах.",
        reply_markup=None  # Убираем клавиатуру запроса контакта
    )
    
    # Показываем главное меню
    await show_main_menu(update, context)
    
    # Планируем уведомления для нового пользователя
    await schedule_user_notifications(user.id)
    
    return ConversationHandler.END

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎬 Ближайшие стримы", callback_data="upcoming_streams")],
        [InlineKeyboardButton("📚 Полезные материалы", callback_data="useful_content")],
        [InlineKeyboardButton("🎓 Наши курсы", callback_data="our_courses")],
        [InlineKeyboardButton("💬 Обратная связь", callback_data="feedback")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Проверяем, откуда был вызван метод
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "Главное меню бота для уведомлений о стримах:", reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "Главное меню бота для уведомлений о стримах:", reply_markup=reply_markup
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "upcoming_streams":
        await show_upcoming_streams(update, context)
    elif query.data == "useful_content":
        await show_useful_content(update, context)
    elif query.data == "our_courses":
        await show_courses(update, context)
    elif query.data == "feedback":
        await request_feedback(update, context)
    elif query.data == "main_menu":
        await show_main_menu(update, context)
    else:
        # Обработка других кнопок
        pass

# Функции для показа информации
async def show_upcoming_streams(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await query.edit_message_text(
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
    
    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def show_useful_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    conn = get_db_connection()
    content_items = conn.execute("""
    SELECT content_id, content_type, title, description, link
    FROM content
    ORDER BY created_at DESC
    LIMIT 5
    """).fetchall()
    conn.close()
    
    if not content_items:
        await query.edit_message_text(
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
        text += "\n"
    
    keyboard = [[InlineKeyboardButton("Назад", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def show_courses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    # Для этого раздела можно также создать таблицу в БД, 
    # но для простоты оставим фиксированный контент
    
    text = "🎓 Наши курсы:\n\n"
    text += "1️⃣ Базовый курс - для начинающих\n"
    text += "👉 https://example.com/basic-course\n\n"
    text += "2️⃣ Продвинутый курс - для опытных\n"
    text += "👉 https://example.com/advanced-course\n\n"
    text += "3️⃣ Мастер-класс - для профессионалов\n"
    text += "👉 https://example.com/master-class\n\n"
    
    keyboard = [[InlineKeyboardButton("Назад", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def request_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    # Получаем последний стрим, на котором был пользователь
    conn = get_db_connection()
    last_stream = conn.execute("""
    SELECT stream_id, title FROM streams 
    WHERE stream_date < datetime('now') 
    ORDER BY stream_date DESC 
    LIMIT 1
    """).fetchone()
    conn.close()
    
    if not last_stream:
        await query.edit_message_text(
            "У нас еще не было стримов, по которым можно оставить обратную связь. "
            "После участия в стриме, вы сможете поделиться своим мнением!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="main_menu")]])
        )
        return
    
    context.user_data['feedback_stream_id'] = last_stream['stream_id']
    
    text = f"Пожалуйста, оставьте обратную связь по стриму \"{last_stream['title']}\"\n\n"
    text += "Напишите ваш отзыв в ответ на это сообщение."
    
    keyboard = [[InlineKeyboardButton("Назад", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def process_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    feedback_text = update.message.text
    
    if 'feedback_stream_id' in context.user_data:
        stream_id = context.user_data['feedback_stream_id']
        
        # Сохраняем обратную связь в базу данных
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            stream_id INTEGER,
            feedback_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute(
            "INSERT INTO feedback (user_id, stream_id, feedback_text) VALUES (?, ?, ?)",
            (user.id, stream_id, feedback_text)
        )
        conn.commit()
        conn.close()
        
        await update.message.reply_text(
            "Спасибо за вашу обратную связь! Мы ценим ваше мнение и используем его для улучшения наших стримов."
        )
        
        # Показываем главное меню
        await show_main_menu(update, context)
        
        # Удаляем из контекста ID стрима
        del context.user_data['feedback_stream_id']
    else:
        await update.message.reply_text(
            "Извините, я не могу обработать эту обратную связь. "
            "Пожалуйста, используйте соответствующую кнопку в меню для отправки обратной связи."
        )
        await show_main_menu(update, context)

# Функции для уведомлений
async def schedule_user_notifications(user_id):
    """Планирует уведомления для пользователя на основе предстоящих стримов"""
    
    conn = get_db_connection()
    
    # Создаем таблицу уведомлений, если она не существует
    conn.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        stream_id INTEGER,
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
        for day in range(min(days_until_stream, 7), 0, -2):  # Каждые 2 дня, но не больше недели
            notification_date = stream_date - timedelta(days=day)
            
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
        
        # Напоминание за час до стрима
        hour_before = stream_date - timedelta(hours=1)
        if hour_before > now:
            conn.execute(
                """
                INSERT INTO notifications 
                (user_id, stream_id, notification_type, scheduled_time) 
                VALUES (?, ?, ?, ?)
                """,
                (user_id, stream_id, 'hour_before', hour_before.strftime('%Y-%m-%d %H:%M:%S'))
            )
        
        # Уведомление во время стрима
        conn.execute(
            """
            INSERT INTO notifications 
            (user_id, stream_id, notification_type, scheduled_time) 
            VALUES (?, ?, ?, ?)
            """,
            (user_id, stream_id, 'during_stream', stream_date.strftime('%Y-%m-%d %H:%M:%S'))
        )
        
        # Уведомление после стрима
        after_stream = stream_date + timedelta(hours=2)
        conn.execute(
            """
            INSERT INTO notifications 
            (user_id, stream_id, notification_type, scheduled_time) 
            VALUES (?, ?, ?, ?)
            """,
            (user_id, stream_id, 'after_stream', after_stream.strftime('%Y-%m-%d %H:%M:%S'))
        )
    
    # Планируем бонусные уведомления (контент)
    content_count = conn.execute("SELECT COUNT(*) FROM content").fetchone()[0]
    
    if content_count > 0:
        # Определяем, сколько бонусных уведомлений планировать
        bonus_count = min(content_count, 10)  # Не более 10 бонусных уведомлений
        
        for i in range(bonus_count):
            # Уведомление каждые 2-3 дня
            bonus_date = now + timedelta(days=i*2 + 1)
            
            conn.execute(
                """
                INSERT INTO notifications 
                (user_id, stream_id, notification_type, scheduled_time) 
                VALUES (?, NULL, ?, ?)
                """,
                (user_id, 'bonus', bonus_date.strftime('%Y-%m-%d %H:%M:%S'))
            )
    
    conn.commit()
    conn.close()

async def send_pending_notifications(bot):
    """Отправляет все запланированные уведомления, время которых уже наступило"""
    
    logger.info("Проверка и отправка уведомлений...")
    
    conn = get_db_connection()
    
    # Получаем все запланированные уведомления, которые нужно отправить
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    notifications = conn.execute("""
    SELECT n.notification_id, n.user_id, n.stream_id, n.notification_type,
           s.title, s.description, s.stream_date, s.is_closed, s.access_link
    FROM notifications n
    LEFT JOIN streams s ON n.stream_id = s.stream_id
    WHERE n.sent = 0 AND n.scheduled_time <= ?
    """, (now,)).fetchall()
    
    logger.info(f"Найдено {len(notifications)} уведомлений для отправки")
    
    for notification in notifications:
        notification_id = notification['notification_id']
        user_id = notification['user_id']
        stream_id = notification['stream_id']
        notification_type = notification['notification_type']
        
        # Готовим текст сообщения в зависимости от типа уведомления
        message_text = ""
        
        if notification_type == 'reminder':
            message_text = f"🔔 Напоминание о предстоящем стриме!\n\n"
            if stream_id:
                message_text += f"📺 {notification['title']}\n"
                message_text += f"📝 {notification['description']}\n"
                
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
            message_text += f"📺 {notification['title']}\n"
            message_text += f"📝 {notification['description']}\n"
            
            # Форматируем время
            try:
                stream_date = datetime.fromisoformat(notification['stream_date'].replace('Z', '+00:00'))
                message_text += f"🕒 Начало в: {stream_date.strftime('%H:%M')}\n"
            except:
                pass
        
        elif notification_type == 'hour_before':
            message_text = f"⏰ Стрим начнется через час!\n\n"
            message_text += f"📺 {notification['title']}\n"
            message_text += f"📝 {notification['description']}\n"
            message_text += f"🔗 Подготовьтесь к просмотру!\n"
        
        elif notification_type == 'during_stream':
            message_text = f"🔴 Мы в эфире!\n\n"
            message_text += f"📺 {notification['title']}\n"
            if notification['is_closed'] and notification['access_link']:
                message_text += f"🔐 Это закрытый стрим. Ваша ссылка для доступа: {notification['access_link']}\n"
        
        elif notification_type == 'after_stream':
            message_text = f"🎬 Спасибо, что были с нами на стриме!\n\n"
            message_text += f"📺 {notification['title']}\n"
            message_text += f"💬 Пожалуйста, оставьте обратную связь, чтобы мы могли улучшить наши стримы.\n"
        
        elif notification_type == 'bonus':
            # Получаем случайный контент
            content = conn.execute("""
            SELECT title, description, link
            FROM content
            ORDER BY RANDOM()
            LIMIT 1
            """).fetchone()
            
            if content:
                message_text = f"🎁 Полезный материал для вас!\n\n"
                message_text += f"📌 {content['title']}\n"
                message_text += f"📝 {content['description']}\n"
                if content['link']:
                    message_text += f"🔗 {content['link']}\n"
            else:
                # Если контента нет, не отправляем уведомление
                conn.execute("UPDATE notifications SET sent = 1 WHERE notification_id = ?", (notification_id,))
                continue
        
        # Отправляем уведомление
        success = await send_message_to_user(bot, user_id, message_text)
        
        # Отмечаем уведомление как отправленное
        if success:
            conn.execute("UPDATE notifications SET sent = 1 WHERE notification_id = ?", (notification_id,))
            logger.info(f"Уведомление {notification_id} отправлено пользователю {user_id}")
        else:
            logger.error(f"Не удалось отправить уведомление {notification_id} пользователю {user_id}")
    
    conn.commit()
    conn.close()

async def notifications_scheduler(application):
    """Фоновая задача для регулярной проверки и отправки уведомлений"""
    while True:
        try:
            await send_pending_notifications(application.bot)
        except Exception as e:
            logger.error(f"Ошибка в планировщике уведомлений: {e}")
        
        # Проверяем наличие новых стримов для планирования уведомлений
        try:
            conn = get_db_connection()
            users = conn.execute("SELECT user_id FROM users").fetchall()
            conn.close()
            
            for user in users:
                await schedule_user_notifications(user['user_id'])
        except Exception as e:
            logger.error(f"Ошибка при планировании уведомлений: {e}")
        
        # Ждем некоторое время перед следующей проверкой
        await asyncio.sleep(60)  # Проверка каждую минуту

def run_notifications_scheduler(application):
    """Запускает планировщик уведомлений в основном цикле событий"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(notifications_scheduler(application))

async def main():
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        stream_id INTEGER,
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
    
    conn.commit()
    conn.close()
    
    # Настраиваем бота
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики команд
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CONTACT: [MessageHandler(filters.CONTACT, process_contact)]
        },
        fallbacks=[CommandHandler('cancel', lambda update, context: ConversationHandler.END)]
    )
    
    application.add_handler(conversation_handler)
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_feedback))
    
    # Запускаем планировщик уведомлений в отдельном потоке
    notification_thread = threading.Thread(
        target=run_notifications_scheduler,
        args=(application,),
        daemon=True
    )
    notification_thread.start()
    
    # Запускаем бота
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    logger.info("Бот запущен и готов к работе!")
    
    try:
        # Держим бота работающим до Ctrl+C
        await application.updater.start_polling()
        await application.idle()
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки, завершение работы...")
        await application.stop()
    finally:
        await application.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
