


from utils import get_current_timestamp
from MemPool import MemPool
import json

class BadgeController:

    def __init__(self):
        self.transaction_counter = 0
        self.last_timestamp = get_current_timestamp()
        self.mempool = MemPool()
        self.account_mapping = self.create_account_leaf_mapping()
    

    def create_account_leaf_mapping(self) -> dict:
        mapping = {}
        with open("initial_state.json", "r") as file:
                users_data = json.load(file)
        index = 0
        for user in users_data["accounts"]:
            mapping[user["address"]] = index
            index += 1
    
    async def form_badge():
        pass
    
        
    
    

