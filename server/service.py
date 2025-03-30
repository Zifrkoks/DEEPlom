from datetime import datetime
import string

from ViewModels import ActionUser
from models import Game


class Service:
    def __init__(self):
        self.ts = int(round(datetime.now().timestamp()))
    parts = list()
    
    def set_transaction(self,tr_id):
        self.transaction = tr_id

    def add_to_transaction(self,user_id:int,game_id:int):
        
        self.parts.append({"u_id":user_id,"g_id":game_id})


    def send_transaction_to_AI(self):
        pass


    