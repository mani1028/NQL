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
    gender = Column(String)

@pytest.fixture
def test_db():
    db_url = "sqlite:///multiturn_test.db"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Add sample data
    session.add_all([
        Student(name="Alice", marks=90, gender="Female"),
        Student(name="Bob", marks=75, gender="Male"),
        Student(name="Charlie", marks=85, gender="Male"),
        Student(name="Diana", marks=95, gender="Female")
    ])
    session.commit()
    
    yield db_url
    
    # Cleanup
    Base.metadata.drop_all(engine)
    if os.path.exists("multiturn_test.db"):
        os.remove("multiturn_test.db")

def test_multi_turn_filtering(test_db):
    bot = ERPBot(test_db)
    session_id = "test_session"
    
    # Turn 1: Initial query
    resp1 = bot.ask("Show students", session_id=session_id)
    assert len(resp1.rows) == 4
    
    # Turn 2: Drill-down by gender
    resp2 = bot.ask("only girls", session_id=session_id)
    # Generated SQL should include the 'students' table and 'Female' filter
    assert "students" in resp2.sql.lower()
    assert "female" in resp2.sql.lower()
    assert len(resp2.rows) == 2
    
    # Turn 3: Further drill-down by marks
    resp3 = bot.ask("above 90 marks", session_id=session_id)
    assert "female" in resp3.sql.lower()
    assert "90" in resp3.sql
    assert len(resp3.rows) == 1
    assert resp3.rows[0]['name'] == "Diana"

def test_multi_turn_limit_sort(test_db):
    bot = ERPBot(test_db)
    session_id = "test_session_2"
    
    # Turn 1: Show students
    bot.ask("Show students", session_id=session_id)
    
    # Turn 2: Highest marks
    resp2 = bot.ask("highest marks", session_id=session_id)
    assert "ORDER BY" in resp2.sql
    assert "DESC" in resp2.sql
    assert resp2.rows[0]['name'] == "Diana"
    
    # Turn 3: Top 2
    resp3 = bot.ask("top 2", session_id=session_id)
    assert len(resp3.rows) == 2
    assert resp3.rows[0]['name'] == "Diana"
    assert resp3.rows[1]['name'] == "Alice"
