import requests
import time
from telegram import Bot
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - 
%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Настройки
BOT_TOKEN = "7503427825:AAH6bVm2IbO_mOZT_WuaoXbAcWvItQNWA4g"
CHECK_INTERVAL = 30  # Проверять каждые 30 секунд

# Инициализация бота
bot = Bot(token=BOT_TOKEN)

def process_admin_messages():
    """Основной цикл проверки и отправки сообщений из админ-панели"""
    
    # URL админ-панели можно изменить на нужный
    admin_url = 
"https://rough-rora-flatloops-eaeed163.koyeb.app/api/bot/receive_message"
    
    logger.info("Запуск проверки сообщений из админ-панели")
    
    while True:
        try:
            # В реальной ситуации здесь был бы запрос к API админ-панели 
для получения сообщений
            # Но так как API не работает, мы можем симулировать отправку
            
            # Доступные сообщения (в реальной системе они были бы получены 
из API)
            # messages = 
requests.get("https://admin-panel-url/api/messages")
            
            # Проверка входящих сообщений пользователей через сервер 
            # Отправка тестового запроса для проверки связи
            try:
                test_data = {
                    "user_id": 123456789,
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "testuser",
                    "text": "Тестовое сообщение от скрипта"
                }
                
                logger.info(f"Отправка тестового запроса на сервер: 
{admin_url}")
                response = requests.post(admin_url, json=test_data)
                logger.info(f"Ответ сервера: {response.status_code} - 
{response.text[:100] if response.text else 'Нет ответа'}")
            except Exception as e:
                logger.error(f"Ошибка при отправке тестового запроса: 
{e}")
            
            # Ждем перед следующей проверкой
            logger.info(f"Ожидание {CHECK_INTERVAL} секунд до следующей 
проверки...")
            time.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            logger.error(f"Ошибка в цикле проверки: {e}")
            time.sleep(10)  # В случае ошибки ждем 10 секунд перед 
повторной попыткой

if __name__ == "__main__":
    process_admin_messages()
