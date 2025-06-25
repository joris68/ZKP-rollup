
from Pydantic_Types import *
from internals.Transaction_Validator import Transaction_Validator
from internals.Queue_manager import Queue_Manager
from internals.Mongo_client import get_mongo_client
import os
import uuid
import time
import logging
import json
import sys

logger = logging.getLogger(__name__)

class Sequence_Mananger:

    def __init__(self):
        self.transaction_validator = Transaction_Validator()
        self.mongo = get_mongo_client()
        self.queue_manager = Queue_Manager()


    async def handel_transaction_submission(self, transactionRequest : TransactionRequest) -> tuple[SubmissionResponse, bool]:
            submisson_id = self.generate_random_id()
            valid : bool = await self.transaction_validator.check_transaction_validity(transactionReq=transactionRequest, submission_id=submisson_id)
            if not valid:
                logger.info(f"Transaction with ID {submisson_id} not valid")
                return (SubmissionResponse(message = "Invalid Transaction", submissionId = submisson_id, valid = False), False)

            logger.info(f"Transaction with submisson_id : {submisson_id} was validated")
            success = await self.queue_manager.add_transaction_to_queue(transactionReq=transactionRequest, submisson_id = submisson_id)
            if success:
                return (SubmissionResponse(message = "Transaction successfully submitted", submissionId = submisson_id, valid = True), False)
            else :
                return (SubmissionResponse(message = "Internal server error", submissionId = submisson_id, valid = True), True)


    
    def generate_random_id(self) -> str:
        return str(uuid.uuid4())
    
    def get_current_timestamp() -> int:
     return int(time.time())
    

    async def on_app_start(self):
       await self.insert_start_users()
       await self.setup_genesis_badge()
    

    def get_state_json(self) -> dict:
        with open("initial_account_state.json", "r") as file:
            state_data = json.load(file)
        logger.info(state_data)
        return state_data
        
    
    async def insert_start_users(self):
        users_collection = self.mongo[os.environ["USERS"]]
        try:
            
            initial_state = self.get_state_json()
            logger.info(initial_state)
            user_dicts = [
                UsersCollection(
                        address=user["pub_key"],
                        balance=user["balance"],
                        latestNonce = 0,
                        transactions = []

                    ).dict()
                    for user in initial_state["accounts"]
                ]
        
            users_collection.insert_many(user_dicts)
            logger.info("Inserted users into the database.")
        except Exception as e:
            logger.info(e)
            sys.exit(1)
    

    async def setup_genesis_badge(self):
        initial_state = self.get_state_json()
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
        badges_pointer = CurrentBadge(currBadgeID = geneisis_badge_id,
                            currMerkleRoot = initial_state["initial_state_root"])
        try:
            badges_pointer_col.insert_one(badges_pointer.dict())
            logger.info("Inserted the genesis pointer")
        except Exception as e:
            logger.error(f"Error inserting genesis badge: {e}")
            sys.exit(1)







        

         
                 
            