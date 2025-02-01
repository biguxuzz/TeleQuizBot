from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton

def get_teacher_main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('📝 Создать вопрос')
    keyboard.add('📊 Просмотр вопросов', '🎥 Загрузить видео')
    keyboard.add('▶️ Запустить тестирование', '📈 Рейтинг студентов')
    keyboard.add('🔄 Сбросить состояния')
    return keyboard

def get_student_main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('📊 Мой рейтинг')
    keyboard.add('❓ Помощь')
    return keyboard

def get_share_contact_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    button = KeyboardButton(text="📱 Поделиться контактом", request_contact=True)
    keyboard.add(button)
    return keyboard

def get_answer_options_keyboard(options):
    keyboard = InlineKeyboardMarkup()
    for i, option in enumerate(options, 1):
        keyboard.add(InlineKeyboardButton(text=f"{i}. {option}", callback_data=f"answer_{i}"))
    return keyboard

def get_sections_keyboard(sections, selected_sections=None):
    """
    Создает клавиатуру с разделами для тестирования.
    
    :param sections: список всех доступных разделов
    :param selected_sections: список выбранных разделов (для отметки)
    :return: InlineKeyboardMarkup
    """
    if selected_sections is None:
        selected_sections = []
        
    markup = InlineKeyboardMarkup()
    for section in sections:
        # Добавляем ✅ к названию, если раздел выбран
        button_text = f"{'✅ ' if section in selected_sections else ''}{section}"
        markup.add(InlineKeyboardButton(
            button_text,
            callback_data=f"section_{section}"
        ))
    
    # Добавляем кнопку подтверждения
    if selected_sections:
        markup.add(InlineKeyboardButton("✅ Подтвердить выбор", callback_data="confirm_sections"))
    
    return markup