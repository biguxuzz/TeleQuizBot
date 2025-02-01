import logging
import os
from datetime import datetime

def setup_logger():
    # Создаем директорию для логов если её нет
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Настраиваем формат логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/bot_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('telegram_quiz_bot')

logger = setup_logger() 