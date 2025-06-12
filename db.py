# db.py

from sqlalchemy import create_engine, Column, String, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database setup
DATABASE_URL = 'sqlite:///agents.db'

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Note(Base):
    __tablename__ = 'notes'
    id = Column(Integer, primary_key=True, index=True)  
    name = Column(String, unique=True, nullable=False)
    content = Column(Text, nullable=False)
    location = Column(String, nullable=False)

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(String, primary_key=True, index=True)
    agent_name = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    chat_history = Column(Text, nullable=True)

# Create tables
Base.metadata.create_all(bind=engine)
