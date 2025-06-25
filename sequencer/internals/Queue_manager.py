from internals.Mongo_client import get_mongo_client
from Pydantic_Types import Transaction, TransactionRequest, TransactionStatus
import os
import logging
import time
import uuid
from pymongo import DESCENDING

logger = logging.getLogger(__name__)

BADGE_SIZE = os.environ["BADGE_SIZE"]

class Queue_Manager(object):

    def __init__(self):
        self.mongo = get_mongo_client()
        self.counter = 0
        self.latestTimeStamp = -1
    

    async def add_transaction_to_queue(self, transactionReq : TransactionRequest, submisson_id : str) -> bool:
        try:
            #with self.mongo.start_session(causal_consistency=True) as session:
              #  with session.start_transaction():
                    trans : Transaction = self._enrich_transaction(transaction_request=transactionReq, submission_id= submisson_id)
                    logger.info(f"starting to insert the transaction into the queue : {trans.transactionId}")
                    trans_col = self.mongo[os.environ["TRANSACTIONS"]]
                    trans_col.insert_one(trans.dict())
                    logger.info("transaction successfully inserted into the queue")
                    users_col = self.mongo[os.environ["USERS"]]
                    users_col.update_one(
                        {"address": trans.sender},
                        {
                            "$inc": {
                                "latestNonce": 1,
                                "balance": -trans.amount
                            },
                            "$push": {
                                "transactions": trans.transactionId
                            }
                        }
                    )
                    
                    users_col.update_one(
                        {"address": trans.receiver},
                        {
                            "$inc": { 
                                "balance": +trans.amount
                            }
                        }
                    )
            
                    self.counter += 1
            
                    logger.info(f"Successfully inserted transaction into queue and updated other collections : {trans.transactionId}")
                    return True

        except Exception as e:
            logger.error(f"An exception occured while inserting a transaction : {e}")
            return False

    async def get_badge_ids_from_queue(self) -> list[Transaction]:
        try:
            #with self.mongo.start_session(causal_consistency=True) as session:
            #     with session.start_transaction():
            trans_col = self.mongo[os.environ["TRANSACTIONS"]]
            results  = trans_col.find(
                {"status": TransactionStatus.PENDING},
            ).sort("recievedAt", DESCENDING).limit(BADGE_SIZE)
            # set the transaction status to INLCUDED
            logger.info("retrieving the next badge of transactions")
            transactions_ids = [res["transactionId"] for res in results ]
            update_result = trans_col.update_many(
                {'transactionId': {'$in': transactions_ids}}, 
                {'$set': {'status': TransactionStatus.INCLUDED}}
            )
            logger.info("changed the status the documents from pending to included")
            self.latestTimeStamp = self.get_current_timestamp()
            self.counter = 0
            return results
        except Exception as e:
            pass
    
    def get_current_counter(self) -> int:
        return self.counter
    
    def get_latest_exe_timestamp(self) -> int:
        return self.latestTimeStamp

    def _enrich_transaction(self, transaction_request: TransactionRequest, submission_id: str) -> Transaction:
        logger.info("Enriching the transaction")

        return Transaction(
            receivedAt=self.get_current_timestamp(),
            submissionId=submission_id,
            transactionId=self.generate_random_id(),
            sender=transaction_request.body.sender,
            receiver=transaction_request.body.receiver,
            nonce=transaction_request.body.nonce,
            signature=transaction_request.signature,
            amount=transaction_request.body.amount,
            status=TransactionStatus.PENDING,
            badgeId=None
        )
    
    def generate_random_id(self) -> str:
        return str(uuid.uuid4())
    
    def get_current_timestamp(self) -> int:
     return int(time.time())