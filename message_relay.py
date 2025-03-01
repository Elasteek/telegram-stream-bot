import requests
import time
import logging
from telegram import Bot
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Настройки
BOT_TOKEN = "7503427825:AAH6bVm2IbO_mOZT_WuaoXbAcWvItQNWA4g"  # Токен вашего бота
ADMIN_URL = "https://rough-rora-flatloops-eaeed163.koyeb.app/api/bot/get_messages"  # URL для получения сообщений
MARK_SENT_URL = "https://rough-rora-flatloops-eaeed163.koyeb.app/api/bot/mark_sent/"  # URL для отметки сообщений
CHECK_INTERVAL = 10  # Интервал проверки в секундах (10 секунд)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)

def check_and_send_messages():
    """
    Проверяет наличие новых сообщений для отправки и отправляет их пользователям
    """
    try:
        # Получаем сообщения для отправки
        logger.info("Проверка новых сообщений для отправки...")
        response = requests.get(ADMIN_URL)
        
        # Проверяем успешность запроса
        if response.status_code == 200:
            messages = response.json()
            logger.info(f"Получено {len(messages)} сообщений для отправки")
            
            # Отправляем каждое сообщение
            for message in messages:
                message_id = message.get('id')
                user_id = message.get('user_id')
                text = message.get('text')
                
                if not user_id or not text:
                    logger.warning(f"Некорректное сообщение: {message}")
                    continue
                
                try:
                    # Отправляем сообщение пользователю
                    bot.send_message(chat_id=user_id, text=text)
                    logger.info(f"Сообщение отправлено пользователю {user_id}: {text[:50]}...")
                    
                    # Отмечаем сообщение как отправленное
                    mark_response = requests.post(f"{MARK_SENT_URL}{message_id}")
                    if mark_response.status_code == 200:
                        logger.info(f"Сообщение {message_id} отмечено как отправленное")
                    else:
                        logger.error(f"Ошибка при отметке сообщения {message_id}: {mark_response.status_code} - {mark_response.text}")
                
                except Exception as e:
                    logger.error(f"Ошибка при отправке сообщения {message_id}: {e}")
            
        else:
            logger.error(f"Ошибка при получении сообщений: {response.status_code} - {response.text}")
    
    except Exception as e:
        logger.error(f"Ошибка в процессе проверки и отправки сообщений: {e}")

def main():
    """
    Основная функция, запускающая цикл проверки и отправки сообщений
    """
    logger.info(f"Запуск сервиса отправки сообщений с интервалом {CHECK_INTERVAL} секунд")
    
    # Проверяем подключение к боту
    try:
        bot_info = bot.get_me()
        logger.info(f"Бот успешно подключен: @{bot_info.username} (ID: {bot_info.id})")
    except Exception as e:
        logger.error(f"Ошибка при подключении к боту: {e}")
        return
    
    # Основной цикл
    while True:
        try:
            check_and_send_messages()
        except Exception as e:
            logger.error(f"Критическая ошибка в цикле: {e}")
        
        # Пауза перед следующей проверкой
        logger.info(f"Ожидание {CHECK_INTERVAL} секунд до следующей проверки...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
