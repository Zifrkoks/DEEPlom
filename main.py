from datetime import timedelta
import os
import queue
import shutil
from typing import List

from dotenv import load_dotenv
from sqlalchemy import create_engine, true
from sqlalchemy.orm import sessionmaker,joinedload

from .models import Base, Card, CartItem, Game, Producer, User
from .ViewModels import AddCard, AddFields, GameCreate, GameUpdate, GetUser, ProducerView, UserAuth, UserCreate
from fastapi import FastAPI, HTTPException, Query, Response,Security, UploadFile
from fastapi.staticfiles import StaticFiles

from fastapi_jwt import JwtAuthorizationCredentials, JwtAccessBearer
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext

load_dotenv()
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins="*",
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"])
app.mount("/images", StaticFiles(directory="images"), name="images")
if not os.path.exists('images'):
    os.makedirs('images')
app.o
access_security = JwtAccessBearer(
    secret_key=os.getenv("JWT_SECRET"), auto_error=True)


pwd_context = CryptContext(schemes="bcrypt", deprecated='auto')
engine = create_engine(
    'mysql+pymysql://user:pass@host/dbname',
    connect_args={
        'ssl': {
            'ssl_ca': '/path/to/server-ca.pem',
            'ssl_cert': '/path/to/client-cert.pem',
            'ssl_key': '/path/to/client-key.pem'
        }
    }
)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

@app.post('/api/login')
async def login(user_auth: UserAuth, response: Response):
    try:
        user = db.query(User).filter(User.username == user_auth.username & User.password == pwd_context.hash(user_auth.password)).one()
        subject = {"user_id":user.id,"username":user.username,"balance":user.balance}
        access_token = access_security.create_access_token(
            subject=subject, expires_delta=timedelta(minutes=float(os.getenv("TOKEN_EXPIRES"))))
        access_security.set_access_cookie(response, access_token)
        return {"access_token": access_token}
    except:
        raise HTTPException(status_code=400, detail="User not found or wrong password")


@app.post("/api/register")
def registration(user_create: UserCreate):
    try:
        user = User()
        user.username = user_create.username
        user.password = pwd_context.hash(user_create.password)
        db.add(user)
        db.commit()
        db.refresh()
        subject = {"user_id":user.id,"username":user.username,"balance":user.balance}
        access_token = access_security.create_access_token(
            subject=subject, expires_delta=timedelta(minutes=float(os.getenv("TOKEN_EXPIRES"))))
        access_security.set_access_cookie( access_token)
        return {"access_token": access_token}
    except:
        raise HTTPException(status_code=400, detail="User already exists")


@app.post("/api/me")
def add_fields_me(add_fields:AddFields,credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:    
        user = db.query(User).filter(User.username == credentials.subject["username"]).one()
        user.address = add_fields.address
        user.number = add_fields.number
        user.country = add_fields.country
        user.firstname = add_fields.firstname
        user.lastname = add_fields.lastname
        user.email = add_fields.email
        db.commit()
        db.refresh()
        return {"result": "ok"}
    except:
        raise HTTPException(status_code=400, detail="User not found")

@app.delete("/api/me")
def delete_me(credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:    
        user = db.query(User).filter(User.username == credentials.subject["username"]).one()
        db.delete(user)
        db.commit()
        db.refresh()
        return {"result": "ok"}
    except:
        raise HTTPException(status_code=400, detail="User not found")


@app.get("/api/me", response_model=GetUser)
def getMe(credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        username = credentials.subject["username"]
        user = db.query(User).options(joinedload(User.cart_items,User.on_sale_games)).filter(User.username == username).one()
        return GetUser(user)
    except:
        raise HTTPException(status_code=400, detail="User not found")
    
def add_card(add_card:AddCard,credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        username = credentials.subject["username"]
        user = db.query(User).options(joinedload(User.cards)).filter(User.username == username).one()
        card = Card()
        card.owner = user
        card.number = add_card.number
        card.cvv = add_card.cvv
        card.date = add_card.date
        db.add(card)
        db.commit()
        db.refresh()
    except:
        raise HTTPException(status_code=400, detail="User not found")

@app.post("/api/balance")
def increase_balance(count:int,credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        user = db.query(User).filter(User.username == credentials.subject["username"]).one()
        user.balance += count
        return {"result": f"balance upped on {count}"}
    except:
        raise HTTPException(status_code=400, detail="User not found")


@app.post("/api/games")
def createGame(game_create:GameCreate, image:UploadFile, credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        file_path = f"images/{image.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        game = Game()
        game.name = game_create.name
        game.description = game_create.description
        game.genre = game_create.genre
        game.picture_url = file_path
        game.producer_name = credentials.subject["username"]
        db.add(game)
        db.commit()
        db.refresh()
        return Response(status_code=200)
    except:
        raise HTTPException(status_code=400, detail="model invalid")
    
@app.put("/api/games")
def UpdateGame(game_create:GameUpdate, image:UploadFile, credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        file_path = f"images/{image.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        game = db.query(Game).filter(Game.id == game_create.id).one()
        if(game.producer_name != credentials.subject["username"]):
            return {"result": f"not edited:you are not owner"}
        game.name = game_create.name
        game.description = game_create.description
        game.genre = game_create.genre
        game.picture_url = file_path
        game.producer_name = credentials.subject["username"]
        db.commit()
        db.refresh()
        return {"result": "ok"}
    except:
        raise HTTPException(status_code=400, detail="model invalid")
    

@app.get("/api/games")
def getGames():
    return db.query(Game).all()

@app.post("/api/games/{game_id}")
def add_to_cart(game_id:int, credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        game = db.query(Game).filter(Game.id == game_id).one()
        user = db.query(User).filter(User.username == credentials.subject["username"]).one()
        item = CartItem()
        item.game = game
        item.user = user
        db.add(item)
        db.commit()
        db.refresh()
        return {"result": "ok"}
    except:
        raise HTTPException(status_code=400, detail="invalid")


@app.delete("/api/games/{game_id}")
def del_to_cart(game_id:int, credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        game = db.query(Game).filter(Game.id == game_id).one()
        user = db.query(User).filter(User.username == credentials.subject["username"]).one()
        db.delete(db.query(CartItem).filter(CartItem.game_id == game.id & CartItem.user_id == user.id).one())
        db.commit()
        db.refresh()
        return {"result": "ok"}
    except:
        raise HTTPException(status_code=400, detail="invalid")




