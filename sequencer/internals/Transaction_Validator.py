from internals.Mongo_client import get_mongo_client
from Pydantic_Types import Transaction

class Transaction_Validator(object):

    def __init__(self):
        self.mongo = get_mongo_client()


    def check_transaction_validity(self, transaction : Transaction) -> bool:
        return True


    
        