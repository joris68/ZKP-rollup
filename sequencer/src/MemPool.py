
from src.AsyncMongoClient import get_mongo_client
from src.Types import Transaction, TransactionStatus, SubmissionResponse
import logging
import os
from pymongo import DESCENDING
import asyncio
from src.TransactionValidator import Transaction_Validator
from src.utils import generate_random_id

logger = logging.getLogger(__name__)

BADGE_SIZE = int(os.environ["BADGE_SIZE"])


class MemPool:
    """
        This class should also save invalid transaction as stated in the zkSync Protocol
    """

    def __init__(self):
        self.mongo_client = get_mongo_client()
        self.validator = Transaction_Validator()
    

    async def insert_into_queue(self, transaction : Transaction, submisson_id) -> SubmissionResponse:
        
        transaction_valid = await self.validator.check_transaction_validity(transaction= transaction, submission_id=submisson_id)
        logger.info(transaction_valid)
        #transaction_valid = True

        async with await self.mongo_client.start_session(causal_consistency=True) as session:
                try:
                    logger.info(f"starting to insert the transaction into the queue ")
                    db = self.mongo_client[os.environ["DB_NAME"]]
                    if transaction_valid:
                        transaction.status = TransactionStatus.PENDING.value
                    else:
                        transaction.status = TransactionStatus.INVALID.value
                    transaction_dict = transaction.model_dump()
                    trans_col = db[os.environ["TRANSACTIONS"]]
                    await trans_col.insert_one(transaction_dict, session=session)
                    logger.info("transaction successfully inserted into the queue")
                    return SubmissionResponse(submission_id = submisson_id, valid = transaction_valid)
                except Exception as e:
                    logger.error(f"Failed to process transaction: {e}")
                    raise e
    
    async def insert_deposit_transaction(self, address : str, amount : int , current_time_stamp : int):
        submission_id = generate_random_id()
        async with await self.mongo_client.start_session(causal_consistency=True) as session:
            try:
                deposit_transaction = Transaction(
                    sender = address,
                    amount = amount,
                    receivedAt = current_time_stamp,
                    submissionId = submission_id,
                    transactionId=None,
                    receiver=None,
                    nonce=None,
                    signature=None,
                    status=TransactionStatus.PENDING.value,
                    badgeId=None,
                    pubKey = None
                )
                db = self.mongo_client[os.environ["DB_NAME"]]
                trans_col = db[os.environ["TRANSACTIONS"]]
                users_col = db[os.environ["USERS"]]
                users_col.insert_one({"address" : address, "balance": amount, "nonce" : 0, "account_updates" :[]})
                logger.info("new account leaf inserted due to deposit transaction")
                trans_col.insert_one(deposit_transaction.model_dump())
                logger.info("deposit transaction successfully included into the mempool queue")
            except Exception as e:
                logger.error(f"Deposit event could not be processed : {e}")
        
    #async def insert_withdraw_transaction(self, )

    async def get_transaction_for_badge(self, last_timestamp = None) -> list[Transaction]:
        async with await self.mongo_client.start_session(causal_consistency=True) as session:
                try:
                    db = self.mongo_client[os.environ["DB_NAME"]]
                    trans_col =  db[os.environ["TRANSACTIONS"]]

                    cursor = None
                    if last_timestamp:
                        cursor = trans_col.find(
                        {
                            "status": TransactionStatus.PENDING.value,
                            "receivedAt": {"$gt": last_timestamp}
                        }
                        ).sort("receivedAt", DESCENDING).limit(BADGE_SIZE)
                    else: 
                        cursor = trans_col.find(
                            {"status": TransactionStatus.PENDING.value},
                        ).sort("receivedAt", DESCENDING).limit(BADGE_SIZE)
                    
                    logger.info("retrieving the next badge of transactions")
                    
                    transactions = []
                    async for doc in cursor:
                        transaction = Transaction(**doc)
                        transactions.append(transaction)

                    transaction_ids = [trans.transactionId for trans in transactions]

                    await trans_col.update_many(
                        {'transactionId': {'$in': transaction_ids}}, 
                        {'$set': {'status': TransactionStatus.INCLUDED.value}},
                        session=session
                    )
                    
                    logger.info("changed the status of the documents from pending to included")
                    return transactions
                
                except Exception as e:
                    logger.error(f"Failed to retrieve badge ids from queue: {e}")
                    return []
    
