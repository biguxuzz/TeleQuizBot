from telebot import TeleBot
from telebot.storage import StateMemoryStorage
from src.database.models import Question, AnswerOption, Video, init_db
from src.bot.keyboards import get_teacher_main_menu, get_sections_keyboard
from src.utils.helpers import is_teacher
from src.database.operations import DatabaseOperations
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.utils.logger import logger
from src.bot.states import StudentStates, TeacherStates
from src.utils.test_utils import send_test_question
from src.utils.state_storage import state_storage, data_storage
import random
from telebot.apihelper import ApiTelegramException

# Создаем сессию и хранилище состояний
session = init_db()
state_storage = StateMemoryStorage()
state_storage.update_types = ['message', 'callback_query']

logger.info(f"Состояния преподавателя инициализированы: {TeacherStates.waiting_for_question}, {TeacherStates.waiting_for_answers}")

def register_handlers(bot: TeleBot):
    logger.info("Начало регистрации обработчиков преподавателя")
    db_ops = DatabaseOperations(session)

    def handle_question(message):
        try:
            logger.info(f"Обработка вопроса: {message.text}")
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['question_text'] = message.text
                logger.info(f"Сохранен текст вопроса: {data['question_text']}")

            # Запрашиваем раздел вопроса
            bot.set_state(message.from_user.id, TeacherStates.waiting_for_section, message.chat.id)
            
            # Получаем доступные разделы
            sections = db_ops.get_available_sections()
            
            # Добавляем возможность создания нового раздела
            sections = sections if sections else []
            sections.append("Создать новый раздел")
            
            # Создаем клавиатуру с разделами
            markup = InlineKeyboardMarkup()
            for section in sections:
                markup.add(InlineKeyboardButton(section, callback_data=f"section_{section}"))
            
            bot.send_message(
                message.chat.id,
                "Выберите раздел для вопроса или создайте новый:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"Ошибка в обработке вопроса: {e}", exc_info=True)
            bot.reply_to(message, "Произошла ошибка. Попробуйте еще раз.")

    def handle_answers(message):
        try:
            logger.info(f"Обработка ответов: {message.text}")
            answers = message.text.split('\n')
            if len(answers) < 2:
                bot.reply_to(message, "Необходимо ввести как минимум два варианта ответа")
                return

            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                question_text = data['question_text']
                section = data.get('section', 'Общие вопросы')  # Добавляем значение по умолчанию
                logger.info(f"Получен текст вопроса из хранилища: {question_text}, раздел: {section}")

            # Создаем вопрос в базе
            logger.info(f"Создаем вопрос с ответами: {answers}")
            db_ops = DatabaseOperations(session)
            db_ops.create_question(
                text=question_text,
                section=section,
                answers=answers
            )
            logger.info("Вопрос успешно создан в базе")

            bot.delete_state(message.from_user.id, message.chat.id)
            bot.send_message(
                message.chat.id,
                "Вопрос успешно создан!",
                reply_markup=get_teacher_main_menu()
            )
        except Exception as e:
            logger.error(f"Ошибка в обработке ответов: {e}", exc_info=True)
            bot.reply_to(message, "Произошла ошибка при создании вопроса")

    def handle_video(message):
        try:
            logger.info("Получено видео")
            if not message.video:
                logger.warning("Видео не получено в сообщении")
                bot.reply_to(message, "Пожалуйста, отправьте видео")
                return

            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['video_file_id'] = message.video.file_id
                logger.info(f"Сохранен file_id видео: {data['video_file_id']}")

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Успех", callback_data="video_success"))
            markup.add(InlineKeyboardButton("Частичный успех", callback_data="video_partial"))
            markup.add(InlineKeyboardButton("Неудача", callback_data="video_failure"))

            bot.send_message(
                message.chat.id,
                "Выберите критерий для видео:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"Ошибка в обработке видео: {e}", exc_info=True)
            bot.reply_to(message, "Произошла ошибка при обработке видео")

    # Регистрируем обработчики команд
    @bot.message_handler(commands=['teacher'])
    def teacher_start(message):
        try:
            logger.info(f"Получена команда /teacher от пользователя {message.from_user.id}")
            if not is_teacher(message.from_user.id):
                logger.warning(f"Попытка доступа без прав преподавателя: {message.from_user.id}")
                bot.reply_to(message, "У вас нет прав преподавателя.")
                return

            bot.send_message(
                message.chat.id,
                "Панель управления преподавателя",
                reply_markup=get_teacher_main_menu()
            )
        except Exception as e:
            logger.error(f"Ошибка в teacher_start: {e}", exc_info=True)
            bot.reply_to(message, "Произошла ошибка")

    # Регистрируем общий обработчик сообщений
    @bot.message_handler(func=lambda message: is_teacher(message.from_user.id), content_types=['text', 'video'])
    def handle_message(message):
        try:
            current_state = bot.get_state(message.from_user.id, message.chat.id)
            logger.info(f"Получено сообщение типа {message.content_type}, текущее состояние: {current_state}")
            
            # Инициализируем db_ops в начале функции
            db_ops = DatabaseOperations(session)

            # Обработка состояний
            if current_state:
                if str(current_state) == str(TeacherStates.waiting_for_question):
                    handle_question(message)
                elif str(current_state) == str(TeacherStates.waiting_for_answers):
                    handle_answers(message)
                elif str(current_state) == str(TeacherStates.waiting_for_section):
                    # Обработка ввода нового раздела
                    logger.info(f"Создание нового раздела: {message.text}")
                    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                        data['section'] = message.text
                        logger.info(f"Сохранен новый раздел: {message.text}")
                    
                    # Переходим к вводу вариантов ответа
                    bot.send_message(
                        message.chat.id,
                        "Введите варианты ответов, каждый с новой строки. Первый вариант будет правильным:"
                    )
                    bot.set_state(message.from_user.id, TeacherStates.waiting_for_answers, message.chat.id)
                elif str(current_state) == str(TeacherStates.waiting_for_video):
                    if message.content_type == 'video':
                        handle_video(message)
                    else:
                        bot.reply_to(message, "Пожалуйста, отправьте видео")
                else:
                    logger.warning(f"Неизвестное состояние: {current_state}")

            # Обработка кнопок меню
            if message.content_type == 'text':
                if message.text == "📝 Создать вопрос":
                    logger.info("Запрошено создание вопроса")
                    bot.set_state(message.from_user.id, TeacherStates.waiting_for_question, message.chat.id)
                    bot.send_message(message.chat.id, "Введите текст вопроса:")
                    return

                elif message.text == "📊 Просмотр вопросов":
                    logger.info("Запрошен просмотр вопросов")
                    try:
                        sections = db_ops.get_available_sections()
                        if not sections:
                            bot.reply_to(message, "Пока нет созданных вопросов")
                            return

                        response = "📋 Список вопросов по разделам:\n\n"
                        for section in sections:
                            questions = db_ops.get_questions_by_section(section)
                            if questions:
                                response += f"📚 Раздел: {section}\n"
                                for i, question in enumerate(questions, 1):
                                    response += f"{i}. {question.text}\n"
                                response += "\n"

                        bot.reply_to(message, response)
                    except Exception as e:
                        logger.error(f"Ошибка при показе вопросов: {e}", exc_info=True)
                        bot.reply_to(message, "Произошла ошибка при получении списка вопросов")
                    return

                elif message.text == "▶️ Запустить тестирование":
                    logger.info("Запрошен запуск тестирования")
                    try:
                        # Очищаем предыдущее состояние
                        bot.delete_state(message.from_user.id, message.chat.id)
                        
                        # Устанавливаем новое состояние
                        bot.set_state(message.from_user.id, TeacherStates.waiting_for_test_sections, message.chat.id)
                        
                        # Инициализируем данные в хранилище
                        if message.from_user.id not in state_storage.data:
                            state_storage.data[message.from_user.id] = {}
                        if message.from_user.id not in state_storage.data[message.from_user.id]:
                            state_storage.data[message.from_user.id][message.from_user.id] = {}
                        
                        teacher_data = state_storage.data[message.from_user.id][message.from_user.id]
                        teacher_data['state'] = str(TeacherStates.waiting_for_test_sections)
                        teacher_data['data'] = {'selected_sections': []}
                        
                        sections = db_ops.get_available_sections()
                        if not sections:
                            bot.reply_to(message, "Нет доступных разделов для тестирования")
                            return
                        
                        logger.info(f"Доступные разделы: {sections}")
                        logger.info(f"Текущее состояние: {bot.get_state(message.from_user.id, message.chat.id)}")
                        logger.info(f"Данные в хранилище: {state_storage.data}")
                        
                        markup = get_sections_keyboard(sections)
                        bot.reply_to(
                            message, 
                            "Выберите разделы для тестирования (можно выбрать несколько):", 
                            reply_markup=markup
                        )
                    except Exception as e:
                        logger.error(f"Ошибка при запуске тестирования: {e}", exc_info=True)
                        bot.reply_to(message, "Произошла ошибка при запуске тестирования")
                    return

                elif message.text == "📈 Рейтинг студентов":
                    logger.info("Запрошен рейтинг студентов")
                    try:
                        scores = db_ops.get_all_scores()
                        if not scores:
                            bot.reply_to(message, "Пока нет данных о рейтинге")
                            return
                        
                        response = "📊 Рейтинг студентов:\n\n"
                        for score in scores:
                            response += f"{score.user.last_name} {score.user.first_name}: {score.points} баллов ({score.section})\n"
                        
                        bot.reply_to(message, response)
                    except Exception as e:
                        logger.error(f"Ошибка при показе рейтинга: {e}", exc_info=True)
                        bot.reply_to(message, "Произошла ошибка при получении рейтинга")
                    return

                elif message.text == "🎥 Загрузить видео":
                    logger.info("Запрошена загрузка видео")
                    bot.set_state(message.from_user.id, TeacherStates.waiting_for_video, message.chat.id)
                    bot.send_message(
                        message.chat.id,
                        "Отправьте видео для загрузки. После загрузки вы сможете выбрать критерий оценки."
                    )
                    return

                elif message.text == "🔄 Сбросить состояния":
                    logger.info("Запрошен сброс состояний")
                    try:
                        # Сбрасываем все состояния
                        state_storage.data.clear()
                        logger.info("Все состояния успешно сброшены")
                        
                        bot.reply_to(
                            message,
                            "✅ Состояния всех пользователей успешно сброшены",
                            reply_markup=get_teacher_main_menu()
                        )
                    except Exception as e:
                        logger.error(f"Ошибка при сбросе состояний: {e}", exc_info=True)
                        bot.reply_to(message, "Произошла ошибка при сбросе состояний")
                    return

        except Exception as e:
            logger.error(f"Ошибка в обработке сообщения учителя: {e}", exc_info=True)
            bot.reply_to(message, "Произошла ошибка. Попробуйте еще раз.")
            bot.delete_state(message.from_user.id, message.chat.id)

    # Обработчик callback-запросов для видео
    @bot.callback_query_handler(func=lambda call: call.data.startswith('video_'))
    def handle_video_criteria(call):
        try:
            logger.info(f"Получен callback для видео: {call.data}")
            criteria = call.data.split('_')[1]
            
            with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
                video_file_id = data['video_file_id']
                logger.info(f"Получен file_id видео из хранилища: {video_file_id}")
            
            db_ops = DatabaseOperations(session)
            db_ops.save_video(
                file_id=video_file_id,
                criteria=criteria
            )
            logger.info(f"Видео сохранено с критерием: {criteria}")
            
            bot.delete_state(call.from_user.id, call.message.chat.id)
            bot.edit_message_text(
                "Видео успешно сохранено!",
                call.message.chat.id,
                call.message.message_id
            )
        except Exception as e:
            logger.error(f"Ошибка в обработке критерия видео: {e}", exc_info=True)
            bot.answer_callback_query(call.id, "Произошла ошибка при сохранении видео")

    # Обработчик для выбора раздела при создании вопроса
    @bot.callback_query_handler(func=lambda call: call.data.startswith('section_') and bot.get_state(call.from_user.id, call.message.chat.id) == TeacherStates.waiting_for_section)
    def handle_section_choice(call):
        try:
            section = call.data.split('section_')[1]
            logger.info(f"Выбран раздел для создания вопроса: {section}")
            
            if section == "Создать новый раздел":
                bot.answer_callback_query(call.id)
                bot.edit_message_text(
                    "Введите название нового раздела:",
                    call.message.chat.id,
                    call.message.message_id
                )
                return
            
            # Инициализируем данные перед сохранением
            bot.set_state(call.from_user.id, TeacherStates.waiting_for_answers, call.message.chat.id)
            with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
                if data is None:
                    data = {}
                data['section'] = section
                logger.info(f"Сохранен раздел: {section}")
            
            # Переходим к вводу вариантов ответа
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                "Введите варианты ответов, каждый с новой строки. Первый вариант будет правильным:",
                call.message.chat.id,
                call.message.message_id
            )
            
        except Exception as e:
            logger.error(f"Ошибка при выборе раздела: {e}", exc_info=True)
            bot.answer_callback_query(call.id, "Произошла ошибка. Попробуйте еще раз.")

    # Обработчик для подтверждения выбора разделов при запуске тестирования
    @bot.callback_query_handler(func=lambda call: call.data == "confirm_sections")
    def handle_confirm_sections(call):
        try:
            # Получаем выбранные разделы из хранилища
            teacher_data = state_storage.data.get(call.from_user.id, {}).get(call.from_user.id, {})
            selected_sections = teacher_data.get('data', {}).get('selected_sections', [])
            
            logger.info(f"Подтверждение выбора разделов для тестирования")
            logger.info(f"Выбранные разделы: {selected_sections}")
            
            if not selected_sections:
                bot.answer_callback_query(call.id, "Не выбрано ни одного раздела!")
                return
            
            # Получаем список студентов
            db_ops = DatabaseOperations(session)
            students = db_ops.get_students()
            logger.info(f"Retrieved {len(students)} students from database")
            
            # Запускаем тестирование для каждого студента
            for student in students:
                try:
                    # Инициализируем данные для студента
                    student_id = student.telegram_id
                    
                    # Сохраняем данные в глобальное хранилище данных
                    if student_id not in data_storage.data:
                        data_storage.data[student_id] = {}
                    
                    # Создаем или обновляем данные студента
                    student_data = {
                        'state': str(StudentStates.waiting_for_answer),
                        'data': {
                            'test_sections': selected_sections.copy(),
                            'current_question_index': 0,
                            'score': 0
                        }
                    }
                    
                    # Сохраняем данные
                    data_storage.data[student_id] = student_data
                    
                    logger.info(f"Инициализированы данные для студента {student_id}: {student_data}")
                    logger.info(f"Структура хранилища данных: {data_storage.data}")
                    
                    # Отправляем сигнал начала тестирования и первый вопрос
                    bot.send_message(student_id, "Начинается тестирование!")
                    send_test_question(bot, student_id, session)
                    
                except Exception as e:
                    logger.error(f"Ошибка при запуске теста для студента {student.telegram_id}: {e}")
                    continue
            
            # Подтверждаем учителю
            bot.edit_message_text(
                "Тестирование запущено для всех студентов!",
                call.message.chat.id,
                call.message.message_id
            )
            
        except Exception as e:
            logger.error(f"Ошибка при подтверждении разделов: {e}")
            bot.answer_callback_query(call.id, "Произошла ошибка при запуске тестирования")

    # Обработчик для выбора разделов при запуске тестирования
    @bot.callback_query_handler(func=lambda call: call.data.startswith('section_') and str(bot.get_state(call.from_user.id, call.message.chat.id)) == str(TeacherStates.waiting_for_test_sections))
    def handle_test_section_choice(call):
        try:
            section = call.data.split('_')[1]
            logger.info(f"Выбран раздел для тестирования: {section}")
            logger.info(f"Текущее состояние: {bot.get_state(call.from_user.id, call.message.chat.id)}")
            
            # Получаем или создаем данные учителя
            if call.from_user.id not in state_storage.data:
                state_storage.data[call.from_user.id] = {}
            if call.from_user.id not in state_storage.data[call.from_user.id]:
                state_storage.data[call.from_user.id][call.from_user.id] = {
                    'state': str(TeacherStates.waiting_for_test_sections),
                    'data': {'selected_sections': []}
                }
            
            teacher_data = state_storage.data[call.from_user.id][call.from_user.id]
            selected_sections = teacher_data['data'].get('selected_sections', [])
            
            logger.info(f"Текущие выбранные разделы: {selected_sections}")
            
            # Обновляем список выбранных разделов
            if section in selected_sections:
                selected_sections.remove(section)
                logger.info(f"Удален раздел: {section}")
            else:
                selected_sections.append(section)
                logger.info(f"Добавлен раздел: {section}")
            
            teacher_data['data']['selected_sections'] = selected_sections
            logger.info(f"Обновлен список выбранных разделов: {selected_sections}")
            
            # Получаем все доступные разделы
            db_ops = DatabaseOperations(session)
            all_sections = db_ops.get_available_sections()
            
            # Обновляем клавиатуру
            markup = get_sections_keyboard(all_sections, selected_sections)
            try:
                bot.edit_message_reply_markup(
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=markup
                )
                logger.info("Клавиатура успешно обновлена")
            except ApiTelegramException as e:
                if "message is not modified" not in str(e):
                    logger.error(f"Ошибка при обновлении клавиатуры: {e}")
                    raise
            
            bot.answer_callback_query(call.id)
            
        except Exception as e:
            logger.error(f"Ошибка при выборе раздела для тестирования: {e}", exc_info=True)
            bot.answer_callback_query(call.id, "Произошла ошибка при выборе раздела")

    logger.info("Завершена регистрация обработчиков преподавателя")