


from email import message
from enum import Enum
from os import name
from models import User
from pydantic import BaseModel

class UserCreate(BaseModel):
    username:str
    password:str
    is_seller:bool
    

class UserAuth(BaseModel):
    username:str
    password:str


class GetUser(BaseModel):
    def __init__(self,user:User):
        self.id =  user.id
        self.username = user.username
        self.balance = user.balance
        self.firstname = user.firstname
        self.lastname = user.lastname
        self.email = user.email
        self.number = user.number
    id:int
    username:str
    balance:int
    firstname:str
    lastname:str
    email:str
    number:str

class GameCreate(BaseModel):
    name:str
    description:str
    genre:str
    producer:str

class GetGame(BaseModel):
    id:int
    name:str
    description:str
    genre:str
    producer:str
    picture_url:str

class CreateResponse(BaseModel):
    result:bool
    message:str
class AddCart:
    game_id:int


class AddFields(BaseModel):
    username:str
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

class ActionUser(Enum):
    CART = "addtpcart"
    VIEW = "view"
