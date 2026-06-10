import pytest
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from nql import ERPBot
import os

Base = declarative_base()

class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    marks = Column(Integer)

class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    student_id = Column(Integer, ForeignKey('students.id'))

@pytest.fixture
def test_db():
    db_url = "sqlite:///test_suite.db"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Add sample data
    s1 = Student(name="Alice", marks=90)
    s2 = Student(name="Bob", marks=75)
    session.add_all([s1, s2])
    session.commit()
    
    yield db_url
    
    # Cleanup
    Base.metadata.drop_all(engine)
    if os.path.exists("test_suite.db"):
        os.remove("test_suite.db")

def test_chat_sql_basic(test_db):
    bot = ERPBot(test_db)
    response = bot.ask("Show students")
    
    assert response.error is None
    assert "students" in response.sql.lower()
    assert len(response.rows) == 2
    assert response.confidence > 0.5

def test_chat_sql_filter(test_db):
    bot = ERPBot(test_db)
    response = bot.ask("Show students above 80 marks")
    
    assert response.error is None
    assert ">" in response.sql
    assert len(response.rows) == 1
    assert response.rows[0]['name'] == "Alice"

def test_chat_sql_no_match(test_db):
    bot = ERPBot(test_db)
    response = bot.ask("What is the weather like?")
    
    assert response.error is not None
    assert response.confidence == 0.0
