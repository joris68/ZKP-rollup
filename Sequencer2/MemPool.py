
from AsyncMongoClient import get_mongo_client
from Types import Transaction, TransactionStatus
import logging
import os
from pymongo import DESCENDING
import asyncio

logger = logging.getLogger(__name__)

BADGE_SIZE = int(os.environ["BADGE_SIZE"])


class MemPool:

    def __init__(self):
        self.mongo_client = get_mongo_client()
    

    async def insert_into_queue(self, transaction : Transaction, submisson_id):
        async with await self.mongo_client.start_session(causal_consistency=True) as session:
            #async with session.start_transaction():
                try:
                    logger.info(f"starting to insert the transaction into the queue ")
                    db = self.mongo_client[os.environ["DB_NAME"]]
                    transaction_dict = transaction.model_dump()
                    trans_col = db[os.environ["TRANSACTIONS"]]
                    await trans_col.insert_one(transaction_dict, session=session)
                    logger.info("transaction successfully inserted into the queue")
                    
                    users_col = db[os.environ["USERS"]]
                    await users_col.update_one(
                        {"address": transaction_dict["sender"]},
                        {
                            "$inc": {
                                "latestNonce": 1,
                                "balance": -transaction_dict["amount"]
                            },
                            "$push": {
                                "transactions": transaction_dict["transactionId"]
                            }
                        },
                        session=session
                    )
                    
                    await users_col.update_one(
                        {"address": transaction_dict["receiver"]},
                        {
                            "$inc": { 
                                "balance": transaction_dict["amount"]
                            }
                        },
                        session=session
                    )
                    logger.info(f"Successfully inserted transaction into queue and updated other collections : {transaction_dict['transactionId']}")
                except Exception as e:
                    logger.error(f"Failed to process transaction: {e}")
            

    async def get_badge_for_badge_size(self, last_timestamp = None) -> list[Transaction]:
        async with await self.mongo_client.start_session(causal_consistency=True) as session:
            #async with session.start_transaction():
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
    




