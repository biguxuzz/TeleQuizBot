from src.database.models import User, Question, Answer, Score, Video, AnswerOption
from sqlalchemy.exc import SQLAlchemyError
from src.utils.logger import logger
from src.utils.exceptions import DatabaseError
from typing import List, Optional
import os
from sqlalchemy.orm import Session

class DatabaseOperations:
    """
    Класс для работы с базой данных.
    
    Предоставляет методы для выполнения основных операций с базой данных,
    включая создание, чтение, обновление и удаление записей.
    """

    def __init__(self, session: Session):
        self.session = session

    def create_user(self, telegram_id: int, first_name: str, last_name: str, 
                   phone: str, is_teacher: bool = False) -> User:
        """
        Создает нового пользователя в базе данных.

        Args:
            telegram_id (int): Telegram ID пользователя
            first_name (str): Имя пользователя
            last_name (str): Фамилия пользователя
            phone (str): Номер телефона
            is_teacher (bool, optional): Является ли преподавателем. По умолчанию False

        Returns:
            User: Созданный объект пользователя

        Raises:
            DatabaseError: При ошибке создания пользователя в базе данных
        """
        try:
            user = User(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                is_teacher=is_teacher
            )
            self.session.add(user)
            self.session.commit()
            logger.info(f"Created new user: {telegram_id}")
            return user
        except SQLAlchemyError as e:
            logger.error(f"Error creating user: {e}")
            self.session.rollback()
            raise DatabaseError("Ошибка при создании пользователя")

    def create_question(self, text: str, section: str, answers: List[str]) -> Question:
        """
        Создает новый вопрос с вариантами ответов.

        Args:
            text (str): Текст вопроса
            section (str): Раздел, к которому относится вопрос
            answers (List[str]): Список вариантов ответов, где первый - правильный

        Returns:
            Question: Созданный объект вопроса

        Raises:
            DatabaseError: При ошибке создания вопроса в базе данных
        """
        try:
            question = Question(text=text, section=section)
            self.session.add(question)
            self.session.flush()  # Получаем ID вопроса

            # Добавляем варианты ответов
            for i, answer_text in enumerate(answers):
                answer = AnswerOption(
                    question_id=question.id,
                    text=answer_text,
                    is_correct=(i == 0)  # Первый ответ считается правильным
                )
                self.session.add(answer)

            self.session.commit()
            logger.info(f"Created new question in section: {section}")
            return question
        except SQLAlchemyError as e:
            logger.error(f"Error creating question: {e}")
            self.session.rollback()
            raise DatabaseError("Ошибка при создании вопроса")

    def register_student(self, telegram_id: int, phone: str) -> User:
        """Регистрирует нового студента"""
        try:
            user = User(
                telegram_id=telegram_id,
                phone=phone,
                is_teacher=False
            )
            self.session.add(user)
            self.session.commit()
            logger.info(f"Registered new student: {telegram_id}")
            return user
        except SQLAlchemyError as e:
            logger.error(f"Error registering student: {e}")
            self.session.rollback()
            raise DatabaseError("Ошибка при регистрации студента")

    def get_available_sections(self) -> List[str]:
        """Получает список всех доступных разделов"""
        try:
            sections = self.session.query(Question.section).distinct().all()
            return [section[0] for section in sections]
        except SQLAlchemyError as e:
            logger.error(f"Error getting sections: {e}")
            raise DatabaseError("Ошибка при получении списка разделов")

    def init_teachers(self):
        """Инициализация преподавателей из переменной окружения"""
        try:
            admin_ids = os.getenv('ADMIN_USER_IDS', '')
            logger.info(f"Initializing teachers with IDs: {admin_ids}")
            
            if not admin_ids:
                logger.warning("No ADMIN_USER_IDS found in environment variables")
                return

            for admin_id in admin_ids.split(','):
                if admin_id.strip():
                    try:
                        admin_id = int(admin_id.strip())
                        user = self.session.query(User).filter_by(telegram_id=admin_id).first()
                        
                        if not user:
                            logger.info(f"Creating new teacher with ID: {admin_id}")
                            user = User(
                                telegram_id=admin_id,
                                first_name="Teacher",
                                last_name="Admin",
                                phone="",
                                is_teacher=True
                            )
                            self.session.add(user)
                            self.session.commit()
                            logger.info(f"Successfully created teacher with ID: {admin_id}")
                        elif not user.is_teacher:
                            logger.info(f"Updating user {admin_id} to teacher status")
                            user.is_teacher = True
                            self.session.commit()
                            logger.info(f"Successfully updated user {admin_id} to teacher status")
                        else:
                            logger.info(f"Teacher with ID {admin_id} already exists")
                            
                    except ValueError as ve:
                        logger.error(f"Invalid admin ID format: {admin_id}, error: {ve}")
                    except Exception as e:
                        logger.error(f"Error processing admin ID {admin_id}: {e}")
                        self.session.rollback()
                        
        except Exception as e:
            logger.error(f"Error in init_teachers: {e}")
            self.session.rollback()
            raise

    def get_user_scores(self, user_id: int) -> List[Score]:
        """Получает все баллы пользователя"""
        try:
            user = self.session.query(User).filter_by(telegram_id=user_id).first()
            if not user:
                return []
            return self.session.query(Score).filter_by(user_id=user.id).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user scores: {e}")
            raise DatabaseError("Ошибка при получении баллов пользователя")

    def get_all_scores(self) -> List[Score]:
        """Получает все баллы всех студентов"""
        try:
            scores = (
                self.session.query(Score)
                .join(User)
                .order_by(User.last_name, User.first_name, Score.section)
                .all()
            )
            return scores
        except SQLAlchemyError as e:
            logger.error(f"Error getting all scores: {e}")
            raise DatabaseError("Ошибка при получении рейтинга")

    def get_questions_by_section(self, section: str) -> List[Question]:
        """Получает все вопросы из указанного раздела"""
        try:
            questions = (
                self.session.query(Question)
                .filter_by(section=section)
                .order_by(Question.id)
                .all()
            )
            return questions
        except SQLAlchemyError as e:
            logger.error(f"Error getting questions by section: {e}")
            raise DatabaseError("Ошибка при получении вопросов")

    def save_video(self, file_id: str, criteria: str) -> Video:
        """
        Сохраняет видео в базе данных.

        Args:
            file_id (str): Идентификатор файла в Telegram
            criteria (str): Критерий видео (success/partial/failure)

        Returns:
            Video: Созданный объект видео

        Raises:
            DatabaseError: При ошибке сохранения видео в базе данных
        """
        try:
            video = Video(
                file_id=file_id,
                criteria=criteria
            )
            self.session.add(video)
            self.session.commit()
            logger.info(f"Saved video with file_id: {file_id}, criteria: {criteria}")
            return video
        except SQLAlchemyError as e:
            logger.error(f"Error saving video: {e}")
            self.session.rollback()
            raise DatabaseError("Ошибка при сохранении видео")

    def get_all_students(self) -> List[User]:
        """
        Получает список всех студентов из базы данных.

        Returns:
            List[User]: Список всех студентов

        Raises:
            DatabaseError: При ошибке получения списка студентов
        """
        try:
            students = (
                self.session.query(User)
                .filter_by(is_teacher=False)
                .order_by(User.last_name, User.first_name)
                .all()
            )
            logger.info(f"Retrieved {len(students)} students from database")
            return students
        except SQLAlchemyError as e:
            logger.error(f"Error getting students list: {e}")
            raise DatabaseError("Ошибка при получении списка студентов")

    def get_answer_options(self, question_id: int) -> List[AnswerOption]:
        """
        Получает варианты ответов для конкретного вопроса.

        Args:
            question_id (int): ID вопроса

        Returns:
            List[AnswerOption]: Список вариантов ответов

        Raises:
            DatabaseError: При ошибке получения вариантов ответов
        """
        try:
            answers = (
                self.session.query(AnswerOption)
                .filter_by(question_id=question_id)
                .order_by(AnswerOption.id)  # Сохраняем порядок вариантов ответов
                .all()
            )
            logger.info(f"Retrieved {len(answers)} answer options for question {question_id}")
            return answers
        except SQLAlchemyError as e:
            logger.error(f"Error getting answer options for question {question_id}: {e}")
            raise DatabaseError("Ошибка при получении вариантов ответов")

    def record_answer(self, student_id: int, question_id: int, answer_number: int, is_correct: bool) -> Answer:
        """
        Записывает ответ студента на вопрос в базу данных.
        """
        try:
            # Получаем объект User по telegram_id
            user = self.get_user_by_id(student_id)
            if not user:
                # Если пользователя нет, создаем его
                user = User(
                    telegram_id=student_id,
                    first_name="Unknown",
                    last_name="Student",
                    phone="",
                    is_teacher=False
                )
                self.session.add(user)
                self.session.commit()  # Сохраняем пользователя
                logger.info(f"Создан новый пользователь с telegram_id {student_id}")

            # Создаем запись об ответе
            answer = Answer(
                user_id=user.id,
                question_id=question_id,
                answer_option_id=answer_number,  # Используем правильное имя поля
                is_correct=is_correct
            )
            self.session.add(answer)
            self.session.commit()
            logger.info(f"Записан ответ для студента {student_id}, вопрос {question_id}: {answer_number} (correct: {is_correct})")
            
            # Если ответ правильный, обновляем счет
            if is_correct:
                question = self.session.query(Question).get(question_id)
                if question:
                    current_score = self.get_user_score(user.id, question.section)
                    new_score = current_score.points + 1 if current_score else 1
                    self.update_or_create_score(user.id, question.section, new_score)
                    logger.info(f"Обновлен счет пользователя {student_id} в разделе {question.section}: {new_score}")
            
            return answer
            
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при записи ответа: {e}")
            self.session.rollback()
            raise DatabaseError("Ошибка при записи ответа")

    def get_question_sections(self, question_id: int) -> List[str]:
        """Получает список разделов для вопроса"""
        question = self.session.query(Question).get(question_id)
        return [question.section] if question else []

    def get_students(self):
        """
        Получает список всех студентов (не преподавателей) из базы данных.
        """
        try:
            students = (
                self.session.query(User)
                .filter(User.is_teacher == False)  # Используем is_teacher вместо role
                .order_by(User.last_name, User.first_name)  # Сортируем по фамилии и имени
                .all()
            )
            logger.info(f"Получено {len(students)} студентов из базы данных")
            return students
        except Exception as e:
            logger.error(f"Ошибка при получении списка студентов: {e}")
            return []

    def get_user_score(self, user_id: int, section: str) -> Optional[Score]:
        """Получает текущий счет пользователя в указанном разделе"""
        return self.session.query(Score).filter(
            Score.user_id == user_id,
            Score.section == section
        ).first()

    def get_user_by_id(self, user_id: int) -> User:
        """Получает пользователя по его telegram_id"""
        return self.session.query(User).filter(User.telegram_id == user_id).first()

    def update_or_create_score(self, user_id: int, section: str, points: int):
        """Обновляет или создает новый счет пользователя"""
        try:
            score = self.get_user_score(user_id, section)
            if score:
                score.points = points
            else:
                score = Score(user_id=user_id, section=section, points=points)
                self.session.add(score)
            self.session.commit()
            logger.info(f"Обновлен счет пользователя {user_id} в разделе {section}: {points} баллов")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при обновлении счета: {e}")
            self.session.rollback()
            return False 