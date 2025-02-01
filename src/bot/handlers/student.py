from telebot import TeleBot
from src.database.models import User, Answer, Score, init_db
from src.bot.keyboards import get_student_main_menu, get_share_contact_keyboard, get_answer_options_keyboard
from src.utils.helpers import is_registered_student, is_teacher
from src.database.operations import DatabaseOperations
from src.utils.logger import logger
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
from src.utils.test_utils import send_test_question
from src.bot.states import StudentStates
from src.utils.state_storage import state_storage, data_storage

session = init_db()

logger.info(f"Состояния инициализированы: {StudentStates.waiting_for_name}, {StudentStates.waiting_for_contact}")

def register_handlers(bot: TeleBot):
    logger.info("Начало регистрации обработчиков студента")

    def get_name(message):
        try:
            logger.info(f"Обработка имени: {message.text}")
            name_parts = message.text.split()
            if len(name_parts) < 2:
                bot.reply_to(message, "Пожалуйста, введите и Фамилию, и Имя через пробел")
                return

            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['last_name'] = name_parts[0]
                data['first_name'] = ' '.join(name_parts[1:])
                logger.info(f"Сохранены данные: {data}")

            bot.set_state(message.from_user.id, StudentStates.waiting_for_contact, message.chat.id)
            bot.send_message(
                message.chat.id,
                "Теперь поделитесь вашим контактом:",
                reply_markup=get_share_contact_keyboard()
            )
        except Exception as e:
            logger.error(f"Ошибка в обработке имени: {e}", exc_info=True)
            bot.reply_to(message, "Произошла ошибка. Попробуйте еще раз.")

    def handle_contact(message):
        logger.info("Получено сообщение с контактом")
        try:
            logger.info(f"Получен контакт: {message.contact}")
            if not message.contact:
                logger.warning("Контакт не получен в сообщении")
                bot.reply_to(message, "Пожалуйста, поделитесь контактом, используя кнопку ниже")
                return

            # Получаем сохраненные данные
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                last_name = data.get('last_name')
                first_name = data.get('first_name')
                logger.info(f"Получены данные: last_name={last_name}, first_name={first_name}")

            # Регистрируем студента
            db_ops = DatabaseOperations(session)
            db_ops.create_user(
                telegram_id=message.from_user.id,
                first_name=first_name,
                last_name=last_name,
                phone=message.contact.phone_number,
                is_teacher=False
            )
            logger.info(f"Студент зарегистрирован: {message.from_user.id}")

            # Очищаем состояние и отправляем сообщение об успехе
            bot.delete_state(message.from_user.id, message.chat.id)
            bot.send_message(
                message.chat.id,
                "Регистрация завершена!",
                reply_markup=get_student_main_menu()
            )
        except Exception as e:
            logger.error(f"Ошибка в обработке контакта: {e}", exc_info=True)
            bot.reply_to(message, "Произошла ошибка. Попробуйте еще раз.")

    # Создаем словарь состояний и их обработчиков
    state_handlers = {
        StudentStates.waiting_for_name: get_name,
        StudentStates.waiting_for_contact: handle_contact
    }

    # Регистрируем обработчик команды /start ПЕРЕД общим обработчиком
    @bot.message_handler(commands=['start'])
    def start(message):
        try:
            logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
            if is_registered_student(message.from_user.id):
                logger.info("Пользователь уже зарегистрирован")
                bot.send_message(
                    message.chat.id,
                    "С возвращением!",
                    reply_markup=get_student_main_menu()
                )
                return
            
            bot.set_state(message.from_user.id, StudentStates.waiting_for_name, message.chat.id)
            logger.info(f"Установлено состояние: {bot.get_state(message.from_user.id, message.chat.id)}")
            bot.send_message(message.chat.id, "Добро пожаловать! Введите ваши Фамилию и Имя:")
        except Exception as e:
            logger.error(f"Ошибка в start: {e}", exc_info=True)
            bot.reply_to(message, "Произошла ошибка. Попробуйте еще раз.")

    # Регистрируем общий обработчик текстовых сообщений и контактов
    @bot.message_handler(func=lambda message: not is_teacher(message.from_user.id), content_types=['text', 'contact'])
    def handle_message(message):
        try:
            logger.info(f"Получено сообщение: {message.text}")
            # Проверяем состояние из хранилища
            stored_data = state_storage.data.get(message.from_user.id, {}).get(message.from_user.id, {})
            stored_state = stored_data.get('state')
            
            # Если получено сообщение о начале тестирования
            if message.text == "Начинается тестирование!":
                logger.info("Получено сообщение о начале тестирования")
                send_test_question(bot, message.from_user.id, session)
                return

            # Обработка кнопок меню
            if message.text == "📊 Мой рейтинг":
                logger.info("Запрошен просмотр рейтинга")
                try:
                    db_ops = DatabaseOperations(session)
                    scores = db_ops.get_user_scores(message.from_user.id)
                    if not scores:
                        bot.reply_to(message, "У вас пока нет результатов тестирования")
                        return

                    response = "📊 Ваши результаты:\n\n"
                    for score in scores:
                        response += f"Раздел '{score.section}': {score.points} баллов\n"
                    
                    bot.reply_to(message, response)
                except Exception as e:
                    logger.error(f"Ошибка при показе рейтинга: {e}", exc_info=True)
                    bot.reply_to(message, "Произошла ошибка при получении рейтинга")
                return

            elif message.text == "❓ Помощь":
                logger.info("Запрошена помощь")
                help_text = (
                    "🎓 Помощь по использованию бота:\n\n"
                    "1️⃣ Для начала работы необходимо зарегистрироваться\n"
                    "2️⃣ После регистрации вы сможете участвовать в тестированиях\n"
                    "3️⃣ Используйте кнопку '📊 Мой рейтинг' для просмотра результатов\n"
                    "4️⃣ При возникновении проблем обратитесь к преподавателю"
                )
                bot.reply_to(message, help_text)
                return

            # Обработка состояний регистрации
            current_state = bot.get_state(message.from_user.id, message.chat.id)
            if current_state:
                if str(current_state) == str(StudentStates.waiting_for_name):
                    get_name(message)
                elif str(current_state) == str(StudentStates.waiting_for_contact):
                    if message.content_type == 'contact':
                        handle_contact(message)
                    else:
                        bot.reply_to(message, "Пожалуйста, используйте кнопку для отправки контакта")

        except Exception as e:
            logger.error(f"Ошибка в обработке сообщения студента: {e}", exc_info=True)
            bot.reply_to(message, "Произошла ошибка. Попробуйте еще раз.")

    def process_answer(user_id: int, answer_number: int):
        try:
            db_ops = DatabaseOperations(session)
            current_question = db_ops.get_current_question(user_id)
            is_correct = answer_number == current_question.correct_answer_number
            db_ops.record_answer(user_id, current_question.id, answer_number, is_correct)
            
            if is_correct:
                bot.send_message(user_id, "✅ Правильно!")
            else:
                bot.send_message(user_id, "❌ Неправильно!")
        except Exception as e:
            logger.error(f"Error processing answer: {e}")
            bot.send_message(user_id, "Произошла ошибка при обработке ответа")

    def send_next_question(user_id: int):
        try:
            db_ops = DatabaseOperations(session)
            question = db_ops.get_next_question(user_id)
            if not question:
                bot.send_message(user_id, "Тестирование завершено!")
                return
            
            bot.send_message(
                user_id,
                question.text,
                reply_markup=get_answer_options_keyboard(question.answers_options)
            )
        except Exception as e:
            logger.error(f"Error sending next question: {e}")
            bot.send_message(user_id, "Произошла ошибка при отправке вопроса")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('answer_'))
    def handle_answer(call):
        try:
            user_id = call.from_user.id
            logger.info(f"Получен ответ на вопрос от пользователя {user_id}")
            logger.info(f"Структура хранилища до обработки: {data_storage.data}")
            
            # Получаем данные пользователя из глобального хранилища данных
            user_data = data_storage.data.get(user_id)
            if not user_data:
                logger.error(f"Нет данных пользователя {user_id} в хранилище")
                bot.answer_callback_query(call.id, "Произошла ошибка. Начните тестирование заново.")
                return
                
            test_data = user_data.get('data', {})
            current_question = test_data.get('current_question')
            answer_mapping = test_data.get('current_answer_mapping', {})
            test_sections = test_data.get('test_sections', [])
            
            if not current_question or not answer_mapping:
                logger.error("Отсутствуют данные о текущем вопросе или вариантах ответа")
                bot.answer_callback_query(call.id, "Произошла ошибка. Начните тестирование заново.")
                return
            
            # Получаем выбранный ответ
            answer_index = int(call.data.split('_')[1])
            selected_answer = answer_mapping.get(answer_index)
            
            if not selected_answer:
                logger.error(f"Не найден ответ с индексом {answer_index}")
                bot.answer_callback_query(call.id, "Произошла ошибка. Начните тестирование заново.")
                return
            
            # Проверяем правильность ответа
            is_correct = selected_answer.is_correct
            
            # Обновляем счет и сохраняем результат в базу
            db_ops = DatabaseOperations(session)
            if is_correct:
                test_data['score'] = test_data.get('score', 0) + 1
                response = "✅ Правильно!"
                # Начисляем баллы за правильный ответ
                for section in test_sections:
                    current_score = db_ops.get_user_score(user_id, section)
                    new_score = current_score.points + 1 if current_score else 1
                    if not db_ops.update_or_create_score(user_id, section, new_score):
                        logger.warning(f"Не удалось обновить счет для пользователя {user_id}")
            else:
                response = "❌ Неправильно!"
            
            # Сохраняем ответ в базу данных
            db_ops.record_answer(
                student_id=user_id,
                question_id=current_question.id,
                answer_number=answer_index,
                is_correct=is_correct
            )
            logger.info(f"Сохранен ответ пользователя {user_id} на вопрос {current_question.id}")
            
            # Обновляем индекс текущего вопроса
            test_data['current_question_index'] = test_data.get('current_question_index', 0) + 1
            
            # Сохраняем обновленные данные
            user_data['data'] = test_data
            data_storage.data[user_id] = user_data
            
            logger.info(f"Обновленные данные пользователя: {user_data}")
            
            # Отправляем ответ пользователю
            bot.answer_callback_query(call.id, response)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
            
            # Отправляем следующий вопрос
            send_test_question(bot, user_id, session)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке ответа: {e}", exc_info=True)
            bot.answer_callback_query(call.id, "Произошла ошибка при обработке ответа")

    logger.info("Завершена регистрация обработчиков студента")