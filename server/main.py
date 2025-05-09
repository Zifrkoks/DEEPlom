import array
from datetime import datetime, timedelta
import email
import json
import os
import random
import shutil
import smtplib
import string
import threading
from typing import List

from dotenv import load_dotenv
import requests
from sqlalchemy import and_, create_engine, func
from sqlalchemy.orm import sessionmaker,joinedload
from sqlalchemy.orm.exc import NoResultFound
from models import Base, Card, CartItem, Game, RestorePass, Transaction, TransactionPart, User,Admin,CreateAdmin
from ViewModels import AddCard, AddFields, GameCreate, GetHistoryModel, UserAuth, UserCreate,AdminData
from fastapi import FastAPI, HTTPException, Response, Security, UploadFile
from fastapi.staticfiles import StaticFiles
from os.path import join, dirname
from dateutil.relativedelta import relativedelta
from fastapi_jwt import JwtAuthorizationCredentials, JwtAccessBearer
from fastapi.middleware.cors import CORSMiddleware
from StatisticService import StatisticService
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
app.mount("/bins", StaticFiles(directory="bins"), name="bins")
if not os.path.exists('bins'):
    os.makedirs('bins')

access_security = JwtAccessBearer(
    secret_key=os.getenv("JWT_SECRET"), auto_error=True)

conn = f"mysql+pymysql://{os.getenv("DB_USER")}:{os.getenv("DB_PASS")}@{os.getenv("DB_HOST")}/{os.getenv("DB")}"
print(conn)
engine = create_engine(conn)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()
CreateAdmin(db)
service = Service()
thread1 = threading.Thread(target=service.send_periodic_requests)
thread1.start()
# service.genUsersAndBuyes(db)
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

@app.get("/api/bought")
def get_bought(credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        print(credentials.subject)
        user_id = credentials.subject["user_id"]
        bought = db.query(Game).join(TransactionPart).filter(TransactionPart.user_id == user_id).filter(Game.id == TransactionPart.game_id).all()

        return bought
    except BaseException as e:
        print(e)
        raise HTTPException(status_code=400, detail="User not found")

@app.get("/api/allbought")
def get_bought(credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        print(credentials.subject)
        user_id = credentials.subject["user_id"]
        results = (db.query(Game, TransactionPart.user_id).join(TransactionPart, Game.id == TransactionPart.game_id).all())

        return results
    except BaseException as e:
        print(e)
        raise HTTPException(status_code=400, detail="User not found")


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
def send_restore_pass(username:str):
    try:
        user = db.query(User).filter(User.username == username).one()
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        db.query(RestorePass).filter(RestorePass.username == username).delete()
        db.commit()
        restore = RestorePass()
        restore.code = random_string
        restore.username = username
        lines = [f"From: {os.getenv("EMAIL_NAME")}", f"To: {', '.join(user.email)}", "",f"your code:{random_string}"]
        msg = "\r\n".join(lines)
        smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
        smtpObj.starttls()
        smtpObj.login(os.getenv("EMAIL_NAME"),os.getenv("EMAIL_PASS"))
        smtpObj.sendmail(os.getenv("EMAIL_NAME"),user.email,msg)
        smtpObj.close()
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
        game = db.query(Game).filter(Game.id == game_id).one()
        user = db.query(User).filter(User.username == credentials.subject["username"]).one()
        db.query(CartItem).filter(CartItem.user_id==credentials.subject["user_id"]).filter(CartItem.game_id==game_id).delete()
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
    games = db.query(Game).join(CartItem).filter(Game.id == CartItem.game_id).filter(CartItem.user_id == credentials.subject["user_id"]).all()
    return games

@app.delete("/api/games/cart/{game_id}")
def del_to_cart(game_id:int, credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        db.query(CartItem).filter(CartItem.user_id == credentials.subject["user_id"]).filter(CartItem.game_id == game_id).delete()
        db.commit()
        return {"result": "ok"}
    except BaseException as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="invalid")

@app.post("/api/games/cart/")
def buy(fullprice:int,credentials: JwtAuthorizationCredentials = Security(access_security)):
    items = db.query(Game).join(CartItem).filter(Game.id == CartItem.game_id).filter(CartItem.user_id == credentials.subject["user_id"]).all()
    user = db.query(User).filter(User.id == credentials.subject["user_id"]).one()
    if(user.balance < fullprice):
        return {"result":"money too small"}
    tr = Transaction()
    for item in items:
        item.sales+=1
        part = TransactionPart()
        part.price = item.price - (item.discount*item.price/100)
        part.commission = part.price*service.commission_service/100
        part.game = item
        part.user = user
        part.transaction_id = tr.id
        db.add(part)
        service.add_to_transaction(user.id,item.id)
    db.add(tr)
    user.balance -= fullprice
    db.query(CartItem).filter(CartItem.user_id == user.id).delete()
    db.commit()
    db.refresh(tr)
    service.set_transaction(tr.id)
    service.send_transaction_to_AI()
    return {"result": "buyed"}

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
        game.discount = game_create.discount
        db.commit()
        
        return {"message": "Game updated", "id": game.id}
    except BaseException as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="model invalid")

@app.get("/api/discount")
def setDiscountAll(discount:int):
    db.query(Game).update({Game.discount: discount})
    db.commit()

@app.get("/api/games/{game_id}")
def GetGame(game_id:int, credentials: JwtAuthorizationCredentials = Security(access_security)):
    game = db.query(Game).filter(Game.id == game_id).one()
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
        return {"message": "Game deleted"}
    except BaseException as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="model invalid")

@app.get("/api/games")
def getGames():
    try:
        games = db.query(Game).all()
        return games
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

@app.post("/api/bins/{game_id}")
def setExe(game_id:int, bins:UploadFile, credentials: JwtAuthorizationCredentials = Security(access_security)):
    game = db.query(Game).filter(Game.id == game_id).one()
    if(game.producer_name != credentials.subject["username"]):
        return {"result": f"not deleted: you are not owner"}
    file_path = f"bins/{bins.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(bins.file, buffer)
    game.bin_url = file_path
    db.commit()
    db.refresh(game)
    return {"result":"ok"}

@app.post("/api/recomendation")
def recomendation(credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        to = f"http://{os.getenv("MODEL_SERVICE")}/recommendation"
        print(to)
        resp = requests.get(to,params={"user_id":credentials.subject["user_id"]})
        print(resp.text)
        return resp
    except BaseException as e:
        print(e)


#//////////////////////////ADMINS/////////////////////////
@app.post('/api/admin/login')
async def loginAdmin(user_auth: UserAuth, response: Response):
    try:
        admin = db.query(Admin).filter(Admin.username == user_auth.username).one()
        if(user_auth.password !=admin.password):
            raise HTTPException(status_code=400, detail="wrong password")
        subject = {"admin_id":admin.id,"username":admin.username,"role":"admin"}
        access_token = access_security.create_access_token(
            subject=subject, expires_delta=timedelta(minutes=float(os.getenv("TOKEN_EXPIRES"))))
        access_security.set_access_cookie(response, access_token)
        print(access_token)
        return {"access_token": access_token}
    except NoResultFound as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="not found")
    except BaseException as e:
        raise HTTPException(status_code=400, detail=f"{e}")
@app.get('/api/admin/forecast')
def GetForecast(credentials: JwtAuthorizationCredentials = Security(access_security)):
    if(credentials.subject["role"] != "admin"):
        raise HTTPException(status_code=400, detail="you are not admin")
    sc = StatisticService(db)
    return sc.ForecastNextYear()

@app.post('/api/admin/statistic/alltime')
def GetShopStatisticAllTime(credentials: JwtAuthorizationCredentials = Security(access_security)):
    if(credentials.subject["role"] != "admin"):
        raise HTTPException(status_code=400, detail="you are not admin")
    all_sales =  db.query(TransactionPart).count()
    on_price =  db.query(func.sum(TransactionPart.price)).scalar()
    commission =  db.query(func.sum(TransactionPart.commission)).scalar()
    return {"sales": all_sales, "sum": on_price,"commission": commission}

@app.post('/api/admin/statistic')
def GetShopStatistic(m:GetHistoryModel,credentials: JwtAuthorizationCredentials = Security(access_security)):
    if(credentials.subject["role"] != "admin"):
        raise HTTPException(status_code=400, detail="you are not admin")
    sc = StatisticService(db)
    if(m.from_year != 0):
        if(m.from_month != 0):
            if(m.from_month > 12 or m.from_month < 1):
                return {"message": "mouth must be from 1 to 12"}
            if(m.from_day != 0):
                if(m.from_day > 31 or m.from_day < 1):
                    return {"message": "day must be from 1 to 31"}
                start_date = datetime(m.from_year, m.from_month, m.from_day)
                if m.to_year != 0 and m.to_month != 0 and m.to_day!= 0:
                    end_date = datetime(m.to_year, m.to_month, m.to_day)
                else:
                    end_date = datetime(m.from_year, m.from_month, m.from_day) + relativedelta(days=1)
            else:
                start_date = datetime(m.from_year, m.from_month, 1)
                end_date = datetime(m.from_year, m.from_month, 1) + relativedelta(months=1)
        else:
            start_date = datetime(m.from_year, 1, 1)
            end_date = datetime(m.from_year, 1, 1)+ relativedelta(years=1)
    else:             
        return {"message": "year cant be 0"}
    return sc.GetStatistic(start_date,end_date)

@app.post('/api/admin/history')
def GetHistory(m:GetHistoryModel,credentials: JwtAuthorizationCredentials = Security(access_security)):
    if(credentials.subject["role"] != "admin"):
        raise HTTPException(status_code=400, detail="you are not admin")
    sc = StatisticService(db)
    if(m.from_year != 0):
        if(m.from_month != 0):
            if(m.from_month > 12 or m.from_month < 1):
                return {"message": "mouth must be from 1 to 12"}
            if(m.from_day != 0):
                if(m.from_day > 31 or m.from_day < 1):
                    return {"message": "day must be from 1 to 31"}
                start_date = datetime(m.from_year, m.from_month, m.from_day)
                if m.to_year != 0 and m.to_month != 0 and m.to_day!= 0:
                    end_date = datetime(m.to_year, m.to_month, m.to_day)
                else:
                    end_date = datetime(m.from_year, m.from_month, m.from_day) + relativedelta(days=1)
            else:
                start_date = datetime(m.from_year, m.from_month, 1)
                end_date = datetime(m.from_year, m.from_month, 1) + relativedelta(months=1)
        else:
            start_date = datetime(m.from_year, 1, 1)
            end_date = datetime(m.from_year, 1, 1)+ relativedelta(years=1)
    else:             
        return {"message": "year cant be 0"}
    return sc.GetHistory(start_date,end_date)

@app.post('/api/admin/users')
def GetUsers(credentials: JwtAuthorizationCredentials = Security(access_security)):
    if(credentials.subject["role"] != "admin"):
        raise HTTPException(status_code=400, detail="you are not admin")
    users = db.query(User).all()
    return {"users": users}


@app.post('/api/admin')
def CreateAdmin(model:AdminData, credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        if(credentials.subject["role"] != "admin"):
            raise HTTPException(status_code=400, detail="you are not admin")
        admin = Admin()
        admin.username = model.username
        admin.password = model.password
        admin.firstname = model.firstname
        admin.lastname = model.lastname
        admin.email = model.email
        admin.number = model.number
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return {"message": "admin created"}
    except BaseException as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="model invalid")

@app.get('/api/admin/me')
def GetMeAdmin( credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        if(credentials.subject["role"] != "admin"):
            raise HTTPException(status_code=400, detail="you are not admin")
        admin_id = credentials.subject["user_id"]
        admin = db.query(Admin).filter(Admin.id == admin_id).one()
        return admin
    except NoResultFound as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="not found")
    except BaseException as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="model invalid")
    
@app.get('/api/admin/{id}')
def GetAdmin(id:int, credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        if(credentials.subject["role"] != "admin"):
            raise HTTPException(status_code=400, detail="you are not admin")
        admin = db.query(Admin).filter(Admin.id == id).one()
        return admin
    except NoResultFound as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="not found")
    except BaseException as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="model invalid")
    
@app.put('/api/admin/{id}')
def UpdateAdmin(id:int,model:AdminData, credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        if(credentials.subject["role"] != "admin"):
            raise HTTPException(status_code=400, detail="you are not admin")
        admin = db.query(Admin).filter(Admin.id == id).one()
        admin.username = model.username
        admin.password = model.password
        admin.firstname = model.firstname
        admin.lastname = model.lastname
        admin.email = model.email
        admin.number = model.number
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return {"message": "admin edited"}
    except NoResultFound as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="not found")
    except BaseException as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="model invalid")

@app.delete('/api/admin/{id}')
def DeleteAdmin(id:int, credentials: JwtAuthorizationCredentials = Security(access_security)):
    try:
        if(credentials.subject["role"] != "admin"):
            raise HTTPException(status_code=400, detail="you are not admin")
        admin = db.query(Admin).filter(Admin.id == id).one()
        db.delete(admin)
        db.commit()
        return {"message": "admin deleted"}
    except NoResultFound as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="not found")
    except BaseException as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="model invalid")

