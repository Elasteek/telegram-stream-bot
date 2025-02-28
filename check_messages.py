import requests
import time
import json
import logging
from telegram import Bot
import os

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = "7503427825:AAH6bVm2IbO_mOZT_WuaoXbAcWvItQNWA4g"  # Токен бота
ADMIN_URL = "https://rough-rora-flatloops-eaeed163.koyeb.app/api/bot/get_messages"  # API для получения сообщений
MARK_SENT_URL = "https://rough-rora-flatloops-eaeed163.koyeb.app/api/bot/mark_sent/"  # API для отметки сообщений
CHECK_INTERVAL = 30  # Интервал проверки в секундах

# Инициализация бота
bot = Bot(token=TOKEN)

def get_messages_to_send():
    """Получает сообщения для отправки из админ-панели"""
    try:
        logger.info("Проверка новых сообщений...")
        response = requests.get(ADMIN_URL)
        if response.status_code == 200:
            messages = response.json()
            logger.info(f"Получено {len(messages)} сообщений для отправки")
            return messages
        else:
            logger.error(f"Ошибка при получении сообщений: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Ошибка при получении сообщений: {e}")
        return []

def mark_message_as_sent(message_id):
    """Отмечает сообщение как отправленное"""
    try:
        url = f"{MARK_SENT_URL}{message_id}"
        response = requests.post(url)
        success = response.status_code == 200
        logger.info(f"Сообщение {message_id} отмечено как отправленное: {success}")
        return success
    except Exception as e:
        logger.error(f"Ошибка при отметке сообщения {message_id}: {e}")
        return False

def send_message(user_id, text):
    """Отправляет сообщение пользователю через Telegram бота"""
    try:
        bot.send_message(chat_id=user_id, text=text)
        logger.info(f"Сообщение отправлено пользователю {user_id}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
        return False

def main():
    """Основной цикл проверки и отправки сообщений"""
    logger.info("Запуск сервиса проверки сообщений...")
    
    while True:
        try:
            # Получаем сообщения для отправки
            messages = get_messages_to_send()
            
            # Отправляем каждое сообщение
            for message in messages:
                message_id = message.get('id')
                user_id = message.get('user_id')
                text = message.get('text')
                
                if user_id and text and message_id:
                    # Отправляем сообщение
                    success = send_message(user_id, text)
                    
                    # Если успешно отправили, отмечаем как отправленное
                    if success:
                        mark_message_as_sent(message_id)
                else:
                    logger.warning(f"Пропуск сообщения из-за отсутствия данных: {message}")
            
        except Exception as e:
            logger.error(f"Ошибка в цикле проверки сообщений: {e}")
        
        # Ждем перед следующей проверкой
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
