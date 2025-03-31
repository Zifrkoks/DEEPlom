from datetime import datetime
import os
import string
from urllib import request

import requests

from models import Game


class Service:
    def __init__(self):
        self.ts = int(round(datetime.now().timestamp()))
    parts = list()
    
    def set_transaction(self,tr_id:int):
        self.transaction = tr_id

    def add_to_transaction(self,user_id:int,game_id:int):
        
        self.parts.append({"u_id":user_id,"g_id":game_id})


    def send_transaction_to_AI(self):
        arr = []
        for v in self.parts:
            part = {
                'timestamp': self.ts,
                'visitorid': v["u_id"],
                'event': "transaction",
                'itemid': v["g_id"],
                "transactionid":self.transaction
            }
            arr.append(part)
        print({"Data": arr})
        resp = requests.post(f"http://{os.getenv("MODEL_SERVICE")}/model_train/",data={"Data": arr}).json()
        print(resp)

    def send_view_to_AI(self,user_id:int,game_id:int):
        part = {
                'timestamp': self.ts,
                'visitorid': user_id,
                'event': "view",
                'itemid': game_id,
                "transactionid":"nan"
            }
        arr = []
        arr.append(part)
        print({"Data": arr})

        resp = requests.post(f"http://{os.getenv("MODEL_SERVICE")}/model_train/",data={"Data": arr}).json()
        print(resp)

    def send_addtocart_to_AI(self, user_id:int,game_id:int):
        part = {
                'timestamp': self.ts,
                'visitorid': user_id,
                'event': "addtocart",
                'itemid': game_id,
                "transactionid":"nan"
            }
        arr = []
        arr.append(part)
        print({"Data": arr})
        resp = requests.post(f"http://{os.getenv("MODEL_SERVICE")}/model_train/",data={"Data": arr}).json()
        print(resp)
        