import pytest
from src.database.operations import DatabaseOperations
from src.utils.exceptions import DatabaseError

def test_create_user(db_ops):
    user = db_ops.create_user(
        telegram_id=123456,
        first_name="Test",
        last_name="User",
        phone="+1234567890"
    )
    assert user.telegram_id == 123456
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.phone == "+1234567890"
    assert not user.is_teacher

def test_create_question(db_ops):
    question = db_ops.create_question(
        text="Test question?",
        section="Test section",
        answers=["Correct answer", "Wrong answer 1", "Wrong answer 2"]
    )
    assert question.text == "Test question?"
    assert question.section == "Test section"
    assert len(question.answers_options) == 3
    assert question.answers_options[0].is_correct

def test_record_answer(db_ops):
    # Сначала создаем необходимые данные
    user = db_ops.create_user(123456, "Test", "User", "+1234567890")
    question = db_ops.create_question(
        "Test question?",
        "Test section",
        ["Correct", "Wrong"]
    )
    
    answer = db_ops.record_answer(
        user_id=user.id,
        question_id=question.id,
        answer_option_id=question.answers_options[0].id,
        is_correct=True
    )
    
    assert answer.is_correct
    assert answer.user_id == user.id
    assert answer.question_id == question.id 