from src.database.models import User, Question, Answer, Score, Video, init_db
from typing import List, Tuple
import random

session = init_db()

def is_teacher(user_id: int) -> bool:
    # Проверка, является ли пользователь преподавателем
    user = session.query(User).filter_by(telegram_id=user_id).first()
    return user and user.is_teacher

def is_registered_student(user_id: int) -> bool:
    # Проверка, зарегистрирован ли студент
    user = session.query(User).filter_by(telegram_id=user_id).first()
    return user and not user.is_teacher

def get_random_question(section: str, user_id: int) -> Tuple[Question, List[str]]:
    # Получение случайного вопроса из раздела
    asked_questions = session.query(Answer).filter_by(user_id=user_id).with_entities(Answer.question_id).all()
    available_questions = session.query(Question).filter_by(section=section).filter(
        ~Question.id.in_(asked_questions)
    ).all()
    
    if not available_questions:
        # Если все вопросы заданы, сбрасываем историю
        session.query(Answer).filter_by(user_id=user_id).delete()
        available_questions = session.query(Question).filter_by(section=section).all()
    
    question = random.choice(available_questions)
    options = [opt.text for opt in question.answers_options]
    random.shuffle(options)
    return question, options

def calculate_score(user_id: int, section: str) -> float:
    # Подсчет баллов студента по разделу
    score = session.query(Score).filter_by(user_id=user_id, section=section).first()
    return score.points if score else 0

def get_video_for_results(correct_answers: int, total_questions: int) -> str:
    # Выбор видео в зависимости от результатов
    if correct_answers == total_questions:
        criteria = 'success'
    elif correct_answers == 0:
        criteria = 'failure'
    else:
        criteria = 'partial'
    
    videos = session.query(Video).filter_by(criteria=criteria).all()
    if videos:
        return random.choice(videos).file_id
    return None

def shuffle_options(options: List[str]) -> List[str]:
    # Перемешивание вариантов ответов
    shuffled = options.copy()
    random.shuffle(shuffled)
    return shuffled 