from datetime import datetime
from enum import Enum
import platform
from tkinter import CASCADE
from sqlalchemy import Date, DateTime, String,BOOLEAN, TIMESTAMP, Boolean, Column, ForeignKey, Integer, Null, Nullable, Table, Text, column, func, null, true,false
from sqlalchemy.orm import DeclarativeBase,relationship
from ast import List
import email
import string


class Base(DeclarativeBase): pass




class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)


class AdminBalance(BaseModel):
    __tablename__ = "admin_balances"
    balance=Column(Integer,default=0)
    admins = relationship("Admin",back_populates="balance")


class Admin(BaseModel):
    __tablename__ = "admins"
    username=Column(String(50), nullable=false, unique=true)
    password=Column(String(128), nullable=false)
    email=Column(String(100))
    number=Column(String(12))
    firstname=Column(String(50))
    lastname=Column(String(50))
    balance_id=Column(Integer, ForeignKey("admin_balances.id"))
    balance = relationship("AdminBalance",back_populates="admins")
    

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
    name= Column(String(50),nullable=false)
    description=Column(Text, nullable=false)
    picture_url=Column(Text)
    bin_url=Column(Text)
    sales=Column(Integer, default=0)
    discount=Column(Integer,default=0)
    genre = Column(Text, nullable=false)
    price= Column(Integer,nullable=false)
    date = Column(DateTime(timezone=True), server_default=func.now())
    producer_name=Column(String(50),ForeignKey("users.username"), nullable=False)
    platforms = Column(String(50),nullable=false)
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
    __tablename__="transaction_parts"
    game_id=Column(Integer, ForeignKey("games.id"))
    transaction_id=Column(Integer,ForeignKey("transactions.id"),nullable=false)
    transaction=relationship("Transaction",back_populates="parts")
    user_id=Column(Integer, ForeignKey("users.id"))
    date_buy=Column(DateTime(timezone=True), server_default=func.now())
    game = relationship("Game",back_populates="transuctions")
    user = relationship("User",back_populates="transuctions")
    price = Column(Integer, nullable=false)
    commission=Column(Integer, nullable=false)



class Transaction(BaseModel):
    __tablename__="transactions"
    parts=relationship("TransactionPart",back_populates="transaction")
    

class RestorePass(BaseModel):
    __tablename__="restores"
    username=Column(String(50), ForeignKey("users.username"),nullable=false)
    code=Column(String(6),nullable=false)



def CreateAdmin(db):
    try:
        admin = Admin()
        admin.username = "admin"
        admin.password = "admin"
        admin.firstname = "firstname"
        admin.lastname = "lastname"
        admin.email = "email@email.email"
        admin.number = "88005553535"
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print("admin created")
    except BaseException as e:
        print("admin exist")


