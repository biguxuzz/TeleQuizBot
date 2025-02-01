import os
from telebot import TeleBot
from dotenv import load_dotenv
from src.database.models import init_db
from src.bot.handlers import teacher, student
from src.database.operations import DatabaseOperations
from src.bot.handlers.student import state_storage
import logging

# Загружаем переменные окружения в начале файла
load_dotenv()

logger = logging.getLogger(__name__)

def main():
    # Проверяем значение
    admin_ids = os.getenv('ADMIN_USER_IDS')
    logger.info(f"Loaded ADMIN_USER_IDS: {admin_ids}")
    
    # Инициализация базы данных
    session = init_db()
    db_ops = DatabaseOperations(session)
    db_ops.init_teachers()
    
    # Сброс всех состояний при запуске
    logger.info("Сброс состояний пользователей")
    # Очищаем все данные в хранилище состояний
    state_storage.data.clear()
    logger.info("Состояния пользователей сброшены")
    
    # Регистрация хэндлеров
    teacher.register_handlers(bot)
    student.register_handlers(bot)
    
    # Запуск бота
    bot.infinity_polling()

if __name__ == '__main__':
    bot = TeleBot(
        os.getenv('TELEGRAM_TOKEN'), 
        state_storage=state_storage,
        use_class_middlewares=True
    )
    main() 