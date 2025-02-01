from telebot.handler_backends import State, StatesGroup

class StudentStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_contact = State()
    waiting_for_answer = State()
    answering_question = State()

class TeacherStates(StatesGroup):
    waiting_for_question = State()
    waiting_for_answers = State()
    waiting_for_section = State()
    waiting_for_video = State()
    waiting_for_video_criteria = State()
    waiting_for_test_sections = State() 