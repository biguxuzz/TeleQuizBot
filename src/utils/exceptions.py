class QuizBotException(Exception):
    """Базовый класс для исключений бота"""
    pass

class DatabaseError(QuizBotException):
    """Ошибки связанные с базой данных"""
    pass

class ValidationError(QuizBotException):
    """Ошибки валидации данных"""
    pass

class AccessDeniedError(QuizBotException):
    """Ошибки доступа"""
    pass 