
from Pydantic_Types import *
from internals.Transaction_Validator import Transaction_Validator
from internals.Mongo_client import get_mongo_client
import os
import uuid
import time
import logging
import json
import sys

logger = logging.getLogger(__name__)

class Sequence__Mananger:

    def __init__(self):
        self.transaction_validator = Transaction_Validator()
        self.mongo = get_mongo_client()


    async def handel_transaction_submission(self, transactionRequest : TransactionRequest) -> (SubmissionResponse, bool):
            submisson_id = self.generate_random_id()
            if not self.transaction_validator.check_transaction_validity(transaction=transactionRequest):
                return [SubmissionResponse(message = "Invalid Transaction", submissionId = submisson_id), True]

            try:
                transaction = self.enrich_transaction(transaction_request= transactionRequest, submission_id=submisson_id)
                users_col = self.mongo.get_collection(os.environ["USERS"])
                users_col.insert_one(transaction)


            except Exception as e:
                 return [SubmissionResponse(message = "Internal Server Error", submissionId = submisson_id), True]
    
    def enrich_transaction(self, transaction_request : TransactionRequest, submission_id : str) -> Transaction:
        return Transaction(
        receivedAt=self.get_current_timestamp(),
        submissionId=submission_id,
        transactionId=self.generate_random_id(),
        sender=transaction_request.sender,
        receiver=transaction_request.receiver,
        nonce=transaction_request.nonce,
        timestamp=transaction_request.timestamp,
        signature=transaction_request.signature,
        amount=transaction_request.amount,
        status=TransactionStatus.SUBMITTED
    )
    
    def generate_random_id(self) -> str:
        return str(uuid.uuid4())
    
    def get_current_timestamp() -> int:
     return int(time.time())
    
    async def init_batch_and_pointer(self):
        pass

    async def on_app_start(self):
       await self.insert_start_users()
       await self.setup_genesis_badge()
    
    async def insert_start_users(self):
        users_collection = self.mongo[os.environ["USERS"]]
        try:
            #inserting test users
            with open("standard_funded_accounts.json", "r") as file:
                users_data = json.load(file)
            user_dicts = [
                UsersCollection(
                        address=user["address"],
                        balance=user["balance"],
                        latestNonce = 0,
                        transactions = []

                    ).dict()
                    for user in users_data
                ]
        
            users_collection.insert_many(user_dicts)
            logger.info("Inserted users into the database.")
        except Exception as e:
            logger.info(e)
            sys.exit(1)
    

    async def setup_genesis_badge(self):
        badges_col = self.mongo[os.environ["BADGES"]]
        geneisis_badge_id = self.generate_random_id()
        # Create the genesis badge
        genesis_badge = TransactionBadge(
            badgeId=geneisis_badge_id,
            status= BadgeStatus.WAITING_FOR_EXECUTION,
            executionCause=None,
            transactions=[],
            nextBadge=None,
            prevBadge=None 
        )

        try:
            badges_col.insert_one(genesis_badge.dict())
            logger.info("Genesis badge inserted successfully.")
        except Exception as e:
            logger.error(f"Error inserting genesis badge: {e}")
            sys.exit(1)
        
        badges_pointer_col = self.mongo.get_collection(os.environ["CURRENT_BADGE"])
        badges_pointer = CurrentBadge(currBadgeID = geneisis_badge_id)
        try:
            badges_pointer_col.insert_one(badges_pointer.dict())
            logger.info("Inserted the genesis pointer")
        except Exception as e:
            logger.error(f"Error inserting genesis badge: {e}")
            sys.exit(1)







        

         
                 
            