import os
import requests
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Функция для отправки сообщений в админ-панель
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

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f"Привет, {user.first_name}! Отправьте мне сообщение для администраторов.")

# Обработчик всех текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    
    # Логируем сообщение
    logger.info(f"Получено сообщение от {user.id} ({user.first_name}): {text}")
    
    # Отправляем сообщение в админ-панель
    send_message_to_admin(
        user.id,
        user.first_name,
        user.last_name if user.last_name else "",
        user.username if user.username else "",
        text
    )
    
    # Отвечаем пользователю
    await update.message.reply_text("Спасибо за ваше сообщение! Администраторы получили его.")

async def main():
    # Создаем и настраиваем бота
    app = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    logger.info("Запускаем бота...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())