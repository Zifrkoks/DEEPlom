


from datetime import datetime
from email import message
from enum import Enum
from os import name
from pydantic import BaseModel

class UserCreate(BaseModel):
    username:str
    password:str
    is_seller:bool
    

class UserAuth(BaseModel):
    username:str
    password:str


class GetUser(BaseModel):
    id:int
    username:str
    balance:int
    firstname:str
    lastname:str
    email:str
    number:str
    cart:dict

class GameCreate(BaseModel):
    name:str
    description:str
    genre:str
    price:int
    platforms:str
    discount:int
class GetGame(BaseModel):
    id:int
    name:str
    description:str
    genre:str
    producer:str
    picture_url:str
    date:datetime

class CreateResponse(BaseModel):
    result:bool
    message:str
class AddCart:
    game_id:int


class AddFields(BaseModel):
    firstname:str
    lastname:str
    email:str
    country:str
    address:str
    number:str


class AddCard(BaseModel):
    number:str
    cvv:str
    date:str

class AdminData(BaseModel):
    username:str
    password:str
    firstname:str
    lastname:str
    email:str
    number:str

class GetHistoryModel(BaseModel):
    from_year:int
    from_month:int
    from_day:int
    to_year:int
    to_month:int
    to_day:int