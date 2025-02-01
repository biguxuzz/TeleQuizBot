from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    phone = Column(String)
    is_teacher = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    answers = relationship("Answer", back_populates="user")
    scores = relationship("Score", back_populates="user")

class Question(Base):
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    text = Column(String)
    section = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    answers_options = relationship("AnswerOption", back_populates="question")
    answers = relationship("Answer", back_populates="question")

class AnswerOption(Base):
    __tablename__ = 'answer_options'
    
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('questions.id'))
    text = Column(String)
    is_correct = Column(Boolean, default=False)
    
    # Связи
    question = relationship("Question", back_populates="answers_options")

class Answer(Base):
    __tablename__ = 'answers'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    question_id = Column(Integer, ForeignKey('questions.id'))
    answer_option_id = Column(Integer)
    is_correct = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="answers")
    question = relationship("Question", back_populates="answers")

class Score(Base):
    __tablename__ = 'scores'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    section = Column(String)
    points = Column(Float, default=0)
    
    # Связи
    user = relationship("User", back_populates="scores")

class Video(Base):
    __tablename__ = 'videos'
    
    id = Column(Integer, primary_key=True)
    file_id = Column(String)
    criteria = Column(String)  # 'success', 'partial', 'failure'
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    engine = create_engine(os.getenv('DATABASE_URL'))
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()