import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота (после тестирования рекомендуется сбросить)
TOKEN = "7503427825:AAH6bVm2IbO_mOZT_WuaoXbAcWvItQNWA4g" # Замените на ваш токен

# URL админ-панели
ADMIN_URL = "https://rough-rora-flatloops-eaeed163.koyeb.app/api/bot/receive_message"

def send_to_admin(user_id, first_name, last_name, username, text):
    data = {
        "user_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "text": text
    }
    print(f"Отправка сообщения: {data}")
    try:
        response = requests.post(ADMIN_URL, json=data)
        print(f"Ответ: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

def start(update: Update, context: CallbackContext) -> None:
    print("Получена команда /start")
    user = update.effective_user
    update.message.reply_text(f"Привет, {user.first_name}! Отправьте сообщение для администраторов.")

def handle_message(update: Update, context: CallbackContext) -> None:
    print(f"Получено сообщение: {update.message.text}")
    user = update.effective_user
    text = update.message.text
    
    send_to_admin(
        user.id,
        user.first_name,
        user.last_name if user.last_name else "",
        user.username if user.username else "",
        text
    )
    
    update.message.reply_text("Спасибо за ваше сообщение! Администраторы получили его.")

def main() -> None:
    print(f"Запуск бота с токеном {TOKEN[:5]}...{TOKEN[-5:]}")
    
    # Создаем Updater и передаем ему токен бота
    updater = Updater(TOKEN)
    
    # Получаем диспетчер для регистрации обработчиков
    dispatcher = updater.dispatcher
    
    # Регистрируем обработчики
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # Запускаем бота
    print("Запуск бота...")
    updater.start_polling()
    print("Бот запущен и готов к работе!")
    
    # Работаем, пока не нажмем Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
