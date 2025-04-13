from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey, UniqueConstraint
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
    photo_file_id = Column(String, nullable=True)

    # отношения
    items = relationship("Item", back_populates="creator")
    favorite_users = relationship("FavoriteUser", back_populates="user", foreign_keys='FavoriteUser.user_id', cascade="all, delete-orphan")
    liked_by = relationship("FavoriteUser", back_populates="favorite_user", foreign_keys='FavoriteUser.favorite_user_id', cascade="all, delete-orphan")
    favorite_items = relationship("FavoriteItem", back_populates="user", cascade="all, delete-orphan")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    type = Column(Enum(ItemType), nullable=False)
    title = Column(String, nullable=False)
    prize = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    field = Column(String, nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    creator = relationship("User", back_populates="items")
    favorites = relationship("FavoriteItem", back_populates="item", cascade="all, delete-orphan")


class FavoriteUser(Base):
    __tablename__ = "favorite_users"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    favorite_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'favorite_user_id', name='unique_favorite_user'),
    )

    user = relationship("User", back_populates="favorite_users", foreign_keys=[user_id])
    favorite_user = relationship("User", back_populates="liked_by", foreign_keys=[favorite_user_id])


class FavoriteItem(Base):
    __tablename__ = "favorite_items"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'item_id', name='unique_favorite_item'),
    )

    user = relationship("User", back_populates="favorite_items")
    item = relationship("Item", back_populates="favorites")
