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
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)

    def __repr__(self):
        return "<{0.__class__.__name__}(id={0.id!r})>".format(self)

class User(BaseModel):
    __table__ = "users"
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
    cart_items = relationship('CartItems',back_populates='carted_by')
    on_sale_games = relationship('Game',back_populates='user')
    


class Game(BaseModel):
    __table__ = "products"
    name= Column(String(100),nullable=false)
    description=Column(Text, nullable=false)
    picture_url=Column(Text,nullable=false)
    genre= Column(Text,nullable=false)
    producer_name=Column(String(100),ForeignKey("users.name"),nullable=false)
    producer=relationship("User",back_populates="games")
    carted_by = relationship('CartItem',back_populates='game')

class CartItem(BaseModel):
    user_id=Column(Integer, ForeignKey("users.id"))
    user = relationship("User",back_populates="cart_items")
    game_id=Column(Integer, ForeignKey("games.id"))
    game = relationship("Game",back_populates="carted_by")

class Action(Enum):
    BUY = "buy"
    CART = "addtpcart"
    VIEW = "view"
    TRANSATION="transaction"

class Card(BaseModel):
    number=Column(String(16))
    cvv=Column(String(3))
    date=Column(String(5))
    owner_id=Column(Integer,ForeignKey("users.id"),nullable=false)
    owner=relationship("User",back_populates="cards")