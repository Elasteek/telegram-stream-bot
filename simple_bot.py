import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Базовая настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Напрямую указываем токен (для тестирования)
BOT_TOKEN = "7503427825:AAH6bVm2IbO_mOZT_WuaoXbAcWvItQNWA4g"

# URL админ-панели для отправки сообщений
ADMIN_PANEL_URL = "https://rough-rora-flatloops-eaeed163.koyeb.app/api/bot/receive_message"

# Функция для отправки сообщений в админ-панель
def send_message_to_admin(user_id, first_name, last_name, username, text):
    data = {
        "user_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "text": text
    }
    
    print(f"Отправка сообщения: {data}")  # Печать в консоль для наглядности
    
    try:
        response = requests.post(ADMIN_PANEL_URL, json=data)
        print(f"Ответ: {response.status_code} - {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

# Обработчик команды /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Получена команда /start")
    user = update.effective_user
    await update.message.reply_text(f"Привет, {user.first_name}! Я бот для отправки сообщений администраторам.")

# Обработчик текстовых сообщений
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Получено сообщение: {update.message.text}")
    
    user = update.effective_user
    text = update.message.text
    
    # Отправляем сообщение в админ-панель
    result = send_message_to_admin(
        user.id,
        user.first_name,
        user.last_name if user.last_name else "",
        user.username if user.username else "",
        text
    )
    
    # Отвечаем пользователю
    if result:
        await update.message.reply_text("Спасибо за ваше сообщение! Администраторы получили его.")
    else:
        await update.message.reply_text("Извините, произошла ошибка при отправке сообщения. Попробуйте позже.")

async def main():
    # Инициализируем бота
    print(f"Инициализация бота с токеном: {BOT_TOKEN[:5]}...{BOT_TOKEN[-5:]}")
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Запускаем бота
    print("Запуск бота...")
    await application.initialize()
    await application.start()
    print("Запуск получения обновлений...")
    await application.updater.start_polling(poll_interval=1.0)
    print("Бот полностью запущен и готов к работе!")
    await application.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
