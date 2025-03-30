from enum import Enum
from tkinter import CASCADE
from sqlalchemy import String,BOOLEAN, TIMESTAMP, Boolean, Column, ForeignKey, Integer, Null, Nullable, Table, Text, column, null, true,false
from sqlalchemy.orm import DeclarativeBase,relationship
from ast import List
import email
import string


class Base(DeclarativeBase): pass




class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)



class User(BaseModel):
    __tablename__ = "users"
    username=Column(String(50), nullable=false, unique=true)
    password=Column(String(128), nullable=false)
    balance=Column(Integer,default=0)
    firstname=Column(String(50))
    lastname=Column(String(50))
    email=Column(String(100))
    country=Column(String(100))
    address=Column(Text)
    number=Column(String(12))
    cards=relationship("Card",back_populates="owner")
    is_seller=Column(BOOLEAN,nullable=false)
    transuctions = relationship('TransactionPart',back_populates='user')
    cart_items = relationship('CartItem',back_populates='user')
    on_sale_games = relationship('Game',back_populates='producer')
    


class Game(BaseModel):
    __tablename__ = "games"
    name= Column(String(100),nullable=false)
    description=Column(Text, nullable=false)
    picture_url=Column(Text,nullable=false)
    genre= Column(Text,nullable=false)
    price= Column(Integer,nullable=false)
    producer_name=Column(String(100),ForeignKey("users.username"),nullable=false)
    producer=relationship("User",back_populates="on_sale_games")
    carted_by = relationship('CartItem',back_populates='game')
    transuctions = relationship('TransactionPart',back_populates='game')
class CartItem(BaseModel):
    __tablename__="cart_items"
    user_id=Column(Integer, ForeignKey("users.id"))
    user = relationship("User",back_populates="cart_items")
    game_id=Column(Integer, ForeignKey("games.id"))
    game = relationship("Game",back_populates="carted_by")


class Card(BaseModel):
    __tablename__="cards"
    number=Column(String(16))
    cvv=Column(String(3))
    date=Column(String(5))
    owner_id=Column(Integer,ForeignKey("users.id"),nullable=false)
    owner=relationship("User",back_populates="cards")



class TransactionPart(BaseModel):
    __tablename__="transactions"
    game_id=Column(Integer, ForeignKey("games.id"))
    transaction=Column(Integer,nullable=false)
    user_id=Column(Integer, ForeignKey("users.id"))
    game = relationship("Game",back_populates="transuctions")
    user = relationship("User",back_populates="transuctions")
