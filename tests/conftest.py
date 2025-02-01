import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base
from src.database.operations import DatabaseOperations
import os

@pytest.fixture(scope="session")
def engine():
    return create_engine('postgresql://test:test@localhost:5432/test_db')

@pytest.fixture(scope="function")
def session(engine):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_ops(session):
    return DatabaseOperations(session) 