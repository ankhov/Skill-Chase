from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

class ItemType(enum.Enum):
    PROJECT = "project"
    HACKATHON = "hackathon"
    TASK = "task"
    CASE_CHAMPIONSHIP = "case_championship"
    OLYMP = "olymp"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    skills = Column(Text, nullable=True)
    about = Column(Text, nullable=True)
    github = Column(String, nullable=True)
    field = Column(String, nullable=True)

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    type = Column(Enum(ItemType), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    field = Column(String, nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    creator = relationship("User", backref="items")