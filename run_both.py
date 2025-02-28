import threading
import subprocess
import os
import sys
import logging
import time
import signal

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("run_both")

# Флаг для управления завершением процессов
should_exit = False

def run_admin_panel():
    """Запускает админ-панель через gunicorn"""
    logger.info("Запуск админ-панели...")
    
    cmd = "gunicorn --bind 0.0.0.0:8080 admin_panel:app"
    admin_process = subprocess.Popen(cmd, shell=True)
    
    logger.info(f"Админ-панель запущена с PID {admin_process.pid}")
    
    # Ждем завершения процесса или флага выхода
    while not should_exit:
        if admin_process.poll() is not None:
            logger.error("Процесс админ-панели неожиданно завершился. Перезапуск...")
            admin_process = subprocess.Popen(cmd, shell=True)
            logger.info(f"Админ-панель перезапущена с PID {admin_process.pid}")
        time.sleep(5)
    
    # Завершаем процесс
    logger.info("Завершение процесса админ-панели...")
    admin_process.terminate()
    admin_process.wait()

def run_telegram_bot():
    """Запускает Telegram-бота"""
    logger.info("Запуск Telegram-бота...")
    
    # Для бота лучше использовать модуль напрямую
    cmd = "python telegram_bot.py"
    bot_process = subprocess.Popen(cmd, shell=True)
    
    logger.info(f"Telegram-бот запущен с PID {bot_process.pid}")
    
    # Ждем завершения процесса или флага выхода
    while not should_exit:
        if bot_process.poll() is not None:
            logger.error("Процесс Telegram-бота неожиданно завершился. Перезапуск...")
            bot_process = subprocess.Popen(cmd, shell=True)
            logger.info(f"Telegram-бот перезапущен с PID {bot_process.pid}")
        time.sleep(5)
    
    # Завершаем процесс
    logger.info("Завершение процесса Telegram-бота...")
    bot_process.terminate()
    bot_process.wait()

def signal_handler(sig, frame):
    """Обработчик сигналов для корректного завершения"""
    global should_exit
    logger.info(f"Получен сигнал {sig}, начинаем завершение работы...")
    should_exit = True

if __name__ == "__main__":
    # Регистрируем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Запускаем админку в отдельном потоке
    admin_thread = threading.Thread(target=run_admin_panel)
    admin_thread.daemon = True
    admin_thread.start()
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_telegram_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    logger.info("Оба сервиса запущены. Нажмите Ctrl+C для завершения.")
    
    # Бесконечный цикл, чтобы держать основной поток запущенным
    try:
        while not should_exit:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания, завершаем работу...")
        should_exit = True
    
    # Ждем завершения потоков
    admin_thread.join(timeout=10)
    bot_thread.join(timeout=10)
    
    logger.info("Сервисы остановлены. Выход.")