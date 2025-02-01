from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.database.operations import DatabaseOperations
from src.utils.logger import logger
from src.bot.states import StudentStates
from src.utils.state_storage import state_storage, data_storage
import random

def send_test_question(bot, user_id, session):
    """
    Отправляет текущий вопрос теста пользователю.
    """
    try:
        logger.info(f"Начало send_test_question для пользователя {user_id}")
        logger.info(f"Данные в хранилище: {data_storage.data}")
        
        # Получаем данные пользователя из глобального хранилища данных
        user_data = data_storage.data.get(user_id, {})
        test_data = user_data.get('data', {})
        test_sections = test_data.get('test_sections', [])
        current_index = test_data.get('current_question_index', 0)
        
        logger.info(f"Полученные данные пользователя: {user_data}")
        logger.info(f"Разделы для тестирования: {test_sections}")
        
        # Получаем вопросы для всех выбранных разделов
        db_ops = DatabaseOperations(session)
        questions = []
        for section in test_sections:
            section_questions = db_ops.get_questions_by_section(section)
            logger.info(f"Получено {len(section_questions)} вопросов для раздела {section}")
            questions.extend(section_questions)
        
        logger.info(f"Всего получено вопросов: {len(questions)}")
        
        if questions and current_index < len(questions):
            current_question = questions[current_index]
            logger.info(f"Текущий вопрос: {current_question.text}")
            
            # Получаем и перемешиваем варианты ответов
            answers = list(db_ops.get_answer_options(current_question.id))
            random.shuffle(answers)
            
            # Сохраняем маппинг ответов и обновляем состояние
            test_data['current_answer_mapping'] = {i: answer for i, answer in enumerate(answers)}
            test_data['current_question'] = current_question
            
            # Обновляем данные в хранилище
            user_data['data'] = test_data
            data_storage.data[user_id] = user_data
            
            logger.info(f"Обновленная структура хранилища: {data_storage.data}")
            
            # Создаем клавиатуру
            markup = InlineKeyboardMarkup()
            for i, answer in enumerate(answers):
                markup.add(InlineKeyboardButton(
                    answer.text,
                    callback_data=f"answer_{i}"
                ))
            
            # Отправляем вопрос
            bot.send_message(
                user_id,
                f"Вопрос {current_index + 1}: {current_question.text}",
                reply_markup=markup
            )
            logger.info(f"Вопрос успешно отправлен пользователю {user_id}")
            
            return True
        else:
            logger.warning(f"Нет доступных вопросов для пользователя {user_id}")
            bot.send_message(user_id, "Тестирование завершено!")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при отправке вопроса: {e}", exc_info=True)
        bot.send_message(user_id, "Произошла ошибка при получении вопроса")
        return False 