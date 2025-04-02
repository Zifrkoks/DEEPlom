from datetime import timedelta
import email
import os
import random
import shutil
import smtplib
import string

from dotenv import load_dotenv
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,joinedload

from models import Base, Card, CartItem, Game, RestorePass, Transaction, TransactionPart, User
from ViewModels import AddCard, AddFields, GameCreate, UserAuth, UserCreate
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
smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
smtpObj.starttls()
smtpObj.login(os.getenv("EMAIL_NAME"),os.getenv("EMAIL_PASS"))

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
        user = db.query(User).options(joinedload(User.cart_items),joinedload(User.cards)).filter(User.id == user_id).one()
        print(user)
        return user
    except BaseException as e:
        print(e)
        raise HTTPException(status_code=400, detail="User not found")


@app.post("/api/restore_pass")
def send_restore_pass(username:str,email:str):
    try:
        user = db.query(User).filter(User.username == username).filter(User.email == email).one()
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        restore = RestorePass()
        restore.code = random_string
        restore.username = username
        lines = [f"From: {os.getenv("EMAIL_NAME")}", f"To: {', '.join(user.email)}", "",f"your code:{random_string}"]
        msg = "\r\n".join(lines)
        smtpObj.sendmail(os.getenv("EMAIL_NAME"),user.email,msg)
        db.query(RestorePass).filter(RestorePass.username == username).delete()
        db.commit()
        db.add(restore)
        db.commit()
        return {"result": "ok"}
    except BaseException as e:
        db.rollback()
        print(e)
        raise HTTPException(status_code=400, detail="User not found")

@app.put("/api/restore_pass")
def input_code(username:str,code:str,newPass:str):
    try:
        restore = db.query(RestorePass).filter(RestorePass.username == username).first()
        if(restore.code != code):
            raise HTTPException(status_code=400, detail="code invalid")
        user = db.query(User).filter(User.username == username).one()
        user.password = newPass
        db.delete(restore)
        db.commit()
        return {"result": "ok"}
    except BaseException as e:
        db.rollback()
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
        return {"result": "ok"}
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

@app.get("/api/games/cart")
def get_cart(credentials: JwtAuthorizationCredentials = Security(access_security)):
    return db.query(Game).join(CartItem).filter(Game.id == CartItem.game_id).filter(CartItem.user_id == credentials.subject["user_id"]).all()

@app.delete("/api/games/cart/{game_id}")
def del_to_cart(game_id:int, credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        db.delete(db.query(CartItem).filter(CartItem.user_id == credentials.subject["user_id"]).filter(CartItem.id == game_id).one())
        db.commit()
        return {"result": "ok"}
    except BaseException as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="invalid")

@app.post("/api/games/cart/")
def buy(credentials: JwtAuthorizationCredentials = Security(access_security)):
    items = db.query(Game).join(CartItem).filter(CartItem.user_id == credentials.subject["username"]).filter(Game.id == CartItem.game_id).all()
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
    service.set_transaction(tr.id)
    service.send_transaction_to_AI()


@app.put("/api/games/{game_id}")
def UpdateGame(game_id:int,game_create:GameCreate, credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        game = db.query(Game).filter(Game.id == game_id).one()
        if(game.producer_name != credentials.subject["username"]):
            return {"result": f"not edited:you are not owner"}
        game.name = game_create.name
        game.description = game_create.description
        game.genre = game_create.genre
        game.price = game_create.price
        game.platforms = game_create.platforms
        db.commit()
        
        return {"message": "Game updated", "id": game.id}
    except BaseException as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="model invalid")
    



@app.get("/api/games/{game_id}")
def GetGame(game_id:int, credentials: JwtAuthorizationCredentials = Security(access_security)):
    game = db.query(Game).filter(Game.id == game_id).one()
    service = Service()
    service.send_view_to_AI(credentials.subject["user_id"],game_id)
    return game



@app.delete("/api/games/{game_id}")
def DeleteGame(game_id:int, credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:    
        game = db.query(Game).filter(Game.id == game_id).one()
        if(game.producer_name != credentials.subject["username"]):
            return {"result": f"not deleted: you are not owner"}
        db.delete(game)
        db.commit()
    except BaseException as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="model invalid")

@app.get("/api/games")
def getGames():
    try:
        return db.query(Game).all()
    except BaseException as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="model invalid")

@app.post("/api/games")
def createGame(game_create:GameCreate,  credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        game = Game()
        game.name = game_create.name
        game.description = game_create.description
        game.genre = game_create.genre
        game.price = game_create.price
        game.producer_name = credentials.subject["username"]
        game.platforms = game_create.platforms
        print(game)
        db.add(game)
        db.commit()
        db.refresh(game)
        return {"message": "Game created", "id": game.id}
    except BaseException as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="model invalid")
@app.post("/api/photo/{game_id}")
def setPhoto(game_id:int, image:UploadFile, credentials: JwtAuthorizationCredentials = Security(access_security)):
    game = db.query(Game).filter(Game.id == game_id).one()
    if(game.producer_name != credentials.subject["username"]):
        return {"result": f"not deleted: you are not owner"}
    file_path = f"images/{image.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    game.picture_url = file_path
    db.commit()
    db.refresh(game)
    return {"result":"ok"}


@app.post("/api/recomendation")
def recomendation(credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        to = f"http://{os.getenv("MODEL_SERVICE")}/recommendation"
        print(to)
        resp = requests.get(to,params={"user_id":credentials.subject["user_id"]}).json()
        return resp
    except BaseException as e:
        print(e)