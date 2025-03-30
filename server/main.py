from datetime import timedelta
import os
import shutil

from dotenv import load_dotenv
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,joinedload

from models import Base, Card, CartItem, Game, Transaction, TransactionPart, User
from ViewModels import AddCard, AddFields, GameCreate, GetUser, UserAuth, UserCreate
from fastapi import FastAPI, HTTPException, Response, Security, UploadFile
from fastapi.staticfiles import StaticFiles
from os.path import join, dirname

from fastapi_jwt import JwtAuthorizationCredentials, JwtAccessBearer
from fastapi.middleware.cors import CORSMiddleware

from service import Service
dotenv_path = join(dirname(__file__), '.env')
load_dotenv()
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins="*",
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"])
app.mount("/images", StaticFiles(directory="images"), name="images")
if not os.path.exists('images'):
    os.makedirs('images')

access_security = JwtAccessBearer(
    secret_key=os.getenv("JWT_SECRET"), auto_error=True)

conn = f"mysql+pymysql://{os.getenv("DB_USER")}:{os.getenv("DB_PASS")}@{os.getenv("DB_HOST")}/{os.getenv("DB")}"
print(conn)
engine = create_engine(conn)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

@app.post('/api/login')
async def login(user_auth: UserAuth, response: Response):
    try:
        user = db.query(User).filter(User.username == user_auth.username).one()
        if(user_auth.password !=user.password):
            raise HTTPException(status_code=400, detail="wrong password")
        subject = {"user_id":user.id,"username":user.username,"balance":user.balance}
        access_token = access_security.create_access_token(
            subject=subject, expires_delta=timedelta(minutes=float(os.getenv("TOKEN_EXPIRES"))))
        access_security.set_access_cookie(response, access_token)
        return {"access_token": access_token}
        print(access_token)
    except BaseException as e:
        raise HTTPException(status_code=400, detail=f"{e}")


@app.post("/api/register")
def registration(user_create: UserCreate,response:Response):
    try:
        user = User()
        user.username = user_create.username
        user.password = user_create.password
        user.is_seller = user_create.is_seller
        db.add(user)
        db.commit()
        db.refresh(user)
        subject = {"user_id":user.id,"username":user.username,"balance":user.balance}
        access_token = access_security.create_access_token(
            subject=subject, expires_delta=timedelta(minutes=float(os.getenv("TOKEN_EXPIRES"))))
        access_security.set_access_cookie(response, access_token)
        return {"access_token": access_token}
    except BaseException as e:
        db.rollback()
        print(e)
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
        return {"result": "ok"}
    except BaseException as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="User not found")

@app.delete("/api/me")
def delete_me(credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:    
        user = db.query(User).filter(User.username == credentials.subject["username"]).one()
        db.delete(user)
        db.commit()
        return {"result": "ok"}
    except:
        db.rollback()
        raise HTTPException(status_code=400, detail="User not found")


@app.get("/api/me")
def getMe(credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        print(credentials.subject)
        user_id = credentials.subject["user_id"]
        user = db.query(User).options(joinedload(User.cart_items)).filter(User.id == user_id).one()
        print(user)
        return user
    except BaseException as e:
        print(e)
        raise HTTPException(status_code=400, detail="User not found")

@app.post("/api/cards")
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
    except BaseException as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="User not found")

@app.post("/api/balance")
def increase_balance(count:int,credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        user = db.query(User).filter(User.username == credentials.subject["username"]).one()
        user.balance += count
        return {"result": f"balance upped on {count}"}
    except BaseException as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="User not found")



@app.post("/api/games/cart/{game_id}")
def add_to_cart(game_id:int, credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        service = Service()
        game = db.query(Game).filter(Game.id == game_id).one()
        user = db.query(User).filter(User.username == credentials.subject["username"]).one()
        item = CartItem()
        item.game = game
        item.user = user
        db.add(item)
        db.commit()
        service.send_addtocart_to_AI(user.id,game.id)
        return {"result": "ok"}

    except BaseException as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="invalid")


@app.delete("/api/games/cart/{game_id}")
def del_to_cart(game_id:int, credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        game = db.query(Game).filter(Game.id == game_id).one()
        user = db.query(User).filter(User.username == credentials.subject["username"]).one()
        db.delete(db.query(CartItem).filter(CartItem.game_id == game.id & CartItem.user_id == user.id).one())
        db.commit()
        return {"result": "ok"}
    except BaseException as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="invalid")

@app.post("/api/games/cart/")
def buy(credentials: JwtAuthorizationCredentials = Security(access_security)):
    items = db.query(Game).filter(Game.carted_by.user_id == credentials.subject["user_id"]).all()
    user = db.query(User).filter(User.id == credentials.subject["user_id"]).one()
    fullprice = 0
    for item in items:
        fullprice += item.price
    if(user.balance < fullprice):
        return {"result":"money too small"}
    tr = Transaction()
    service = Service()
    for item in items:
        part = TransactionPart()
        part.game = item
        part.user = user
        tr.parts.append(item)
        service.add_to_transaction(user.id,item.id)
    db.add(tr)
    db.commit()
    db.refresh(tr)
    service.setTr(tr.id)
    service.send_transaction_to_AI()




@app.put("/api/games/{game_id}")
def UpdateGame(game_id:int,game_create:GameCreate, image:UploadFile, credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        file_path = f"images/{image.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        game = db.query(Game).filter(Game.id == game_id).one()
        if(game.producer_name != credentials.subject["username"]):
            return {"result": f"not edited:you are not owner"}
        game.name = game_create.name
        game.description = game_create.description
        game.genre = game_create.genre
        game.picture_url = file_path
        game.producer_name = credentials.subject["username"]
        db.commit()
        return {"result": "ok"}
    except BaseException as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="model invalid")
    



@app.get("/api/games/{game_id}")
def GetGame(game_id:int, credentials: JwtAuthorizationCredentials = Security(access_security)):
    db.query(Game).filter(Game.id == game_id).one()
    service = Service()
    service.send_view_to_AI(credentials.subject["user_id"],game_id)



@app.get("/api/games/{game_id}")
def DeleteGame(game_id:int, credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:    
        game = db.query(Game).filter(Game.id == game_id).one()
        if(game.producer_name != credentials.subject["username"]):
            return {"result": f"not deleted: you are not owner"}
        db.delete(game)
        db.commit()
    except:
        db.rollback()
        raise HTTPException(status_code=400, detail="model invalid")

@app.get("/api/games")
def getGames():
    try:
        return db.query(Game).all()
    except:
        db.rollback()
        raise HTTPException(status_code=400, detail="model invalid")

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
        return Response(status_code=200)
    except:
        db.rollback()
        raise HTTPException(status_code=400, detail="model invalid")
    

@app.post("/api/recomendation")
def recomendation(credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        resp = requests.get(f"https://{os.getenv("MODEL_SERVICE")}/recommendation",params={"user_id":credentials.subject["user_id"]}).json()
        return resp
    except BaseException as e:
        print(e)