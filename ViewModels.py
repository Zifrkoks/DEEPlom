


from email import message
from os import name
from .models import Producer, User


class UserCreate:
    username:str
    password:str
    is_seller:bool
    

class UserAuth:
    username:str
    password:str


class GetUser:
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

class GameCreate:
    name:str
    description:str
    genre:str
    producer:str
class GameUpdate:
    id:int
    name:str
    description:str
    genre:str
    producer:str
class GetGame:
    id:int
    name:str
    description:str
    genre:str
    producer:str
    picture_url:str

class CreateResponse:
    result:bool
    message:str
class AddCart:
    game_id:int


class AddFields:
    username:str
    firstname:str
    lastname:str
    email:str
    country:str
    address:str
    number:str


class AddCard:
    number:str
    cvv:str
    date:str