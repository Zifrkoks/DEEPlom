from datetime import datetime, timedelta
import time
import json
import math
import os
import string
from urllib import request

import requests

from models import Game


class Service:
    def __init__(self):
        self.arr = []
        self.parts = list()
    def set_transaction(self,tr_id:int):
        self.transaction = tr_id

    def add_to_transaction(self,user_id:int,game_id:int):
        
        self.parts.append({"u_id":user_id,"g_id":game_id})


    def send_transaction_to_AI(self):
        ts = int((datetime.now().timestamp()*1000))

        for v in self.parts:
            part = {
                "timestamp": ts,
                "visitorid": v["u_id"],
                "event": "transaction",
                "itemid": v["g_id"],
                "transactionid":self.transaction
            }
            self.arr.append(part)

    def send_view_to_AI(self,user_id:int,game_id:int):
        ts = int((datetime.now().timestamp()*1000))
        part = {
                "event": "view",
                "transactionid": math.nan,
                "timestamp": ts,
                "visitorid": user_id,
                "itemid": game_id,
            }
        self.arr.append(part)
        

    def send_addtocart_to_AI(self, user_id:int,game_id:int):
        ts = int((datetime.now().timestamp()*1000))
        part = {
                "timestamp": ts,
                "visitorid": user_id,
                "event": "addtocart",
                "itemid": game_id,
                "transactionid": math.nan
            }
        self.arr.append(part)
        

    def send_periodic_requests(self):
        """
        Отправляет post-запрос на указанный URL каждые сутки.
        """
        interval_seconds = 24 * 3600
        while True:
            next_run = datetime.now() + timedelta(seconds=interval_seconds)
            print(f"Следующий запрос в {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(interval_seconds)
            try:
                datas = json.dumps({"Data": self.arr})
                print(f"[{datetime.now()}] Отправка запроса...")
                response = requests.post(f"http://{os.getenv("MODEL_SERVICE")}/model_train/",data=datas).json()
                print(f"Результат: HTTP {response.status_code}")
                
            except Exception as e:
                print(f"Ошибка: {str(e)}")
                
            # Вычисляем время до следующего запуска
            
