import pytest
from unittest.mock import Mock, patch
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.bot.handlers import teacher, student
from src.utils.helpers import is_teacher
from src.bot.handlers.teacher import TeacherStates
from src.utils.logger import logger
from src.database.operations import DatabaseOperations
from src.database.models import init_db

session = init_db()
db_ops = DatabaseOperations(session)

@pytest.fixture
def bot():
    return Mock(spec=TeleBot)

def test_teacher_start(bot):
    message = Mock()
    message.from_user.id = 123456
    message.chat.id = 123456
    
    with patch('src.utils.helpers.is_teacher', return_value=True):
        teacher.register_handlers(bot)
        handler = bot.message_handler(commands=['teacher'])
        handler(message)
        
        bot.send_message.assert_called_once()
        assert "Панель управления преподавателя" in bot.send_message.call_args[0][1]

def test_student_registration(bot):
    message = Mock()
    message.from_user.id = 123456
    message.chat.id = 123456
    
    with patch('src.utils.helpers.is_registered_student', return_value=False):
        student.register_handlers(bot)
        handler = bot.message_handler(commands=['start'])
        handler(message)
        
        bot.send_message.assert_called_once()
        assert "Добро пожаловать" in bot.send_message.call_args[0][1] 

@bot.message_handler(func=lambda m: m.text == "🎥 Загрузить видео" and is_teacher(m.from_user.id))
def upload_video(message):
    bot.set_state(message.from_user.id, TeacherStates.waiting_for_video)
    bot.send_message(
        message.chat.id,
        "Отправьте видео-комментарий:"
    )

@bot.message_handler(content_types=['video'], state=TeacherStates.waiting_for_video)
def process_video(message):
    try:
        file_id = message.video.file_id
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Успех", callback_data="video_success"))
        markup.add(InlineKeyboardButton("Частичный успех", callback_data="video_partial"))
        markup.add(InlineKeyboardButton("Неудача", callback_data="video_failure"))
        
        bot.send_message(
            message.chat.id,
            "Выберите критерий для видео:",
            reply_markup=markup
        )
        # Сохраняем file_id во временное хранилище
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        bot.reply_to(message, "Произошла ошибка при обработке видео")

@bot.message_handler(func=lambda m: m.text == "📈 Рейтинг студентов" and is_teacher(m.from_user.id))
def show_ratings(message):
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
        logger.error(f"Error showing ratings: {e}")
        bot.reply_to(message, "Произошла ошибка при получении рейтинга")