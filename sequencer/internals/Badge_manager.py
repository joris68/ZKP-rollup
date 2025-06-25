
from internals.Queue_manager import Queue_Manager
from internals.Mongo_client import get_mongo_client
from Pydantic_Types import *
import os

BADGE_SIZE = os.environ["BADGE_SIZE"]

class Badge_Manager:

    def __init__(self):
        self.queue_manager = Queue_Manager()
        self.mongo = get_mongo_client()
        

    async def handle_transaction_insertion(self, transactionReq : TransactionRequest):
        success = await self.queue_manager.add_transaction_to_queue()

        if self.queue_manager.counter == BADGE_SIZE:
            pass
        


    
        