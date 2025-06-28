


from utils import get_current_timestamp
from MemPool import MemPool
from Types import BadgeExecutionCause, TransactionBadge, TransactionStatus, BadgeStatus, Transaction
from AsyncMongoClient import get_mongo_client
import logging
from MerkleTreeController import MerkleTreeController
from utils import generate_random_id
import os
import hashlib
import asyncio
from create_test_transactions import create_transaction



#TODO dont forget to reset the badge
#TODO register a task

logger = logging.getLogger(__name__)

"""
    Blocknumber increments monotonically
    Blockhash is determined by the : H(bocknumber, _blocktimestamp, _prevL2BlockHash, _blockTxsRollingHash)
    Rolling: H(H(0, t_1), t_2) ....
"""

class BadgeController:

    def __init__(self):
        self.transaction_counter = 0
        self.last_timestamp = get_current_timestamp()
        self.mempool = MemPool()
        self.mongo_client = get_mongo_client()
        self.tree_controller = MerkleTreeController()
    
    
    async def form_new_L2_block(self, execution_cause : BadgeExecutionCause) -> TransactionBadge:
        logger.info("starting to form new L2 block ")
        try:
            badge_id = generate_random_id()
            transaction_for_badge = None
            if execution_cause == BadgeExecutionCause.FILLEDUP:
                transaction_for_badge = await self.mempool.get_transaction_for_badge()
            else:
                transaction_for_badge = await self.mempool.get_transaction_for_badge(last_timestamp=self.last_timestamp)

            self.last_timestamp = get_current_timestamp()
            logger.info(f"retrived : {len(transaction_for_badge)} transaction for badge : {badge_id}")
            
            for t in transaction_for_badge:
                try:
                    await self.tree_controller.make_rollup_transaction_between_existing_users(badge_id=badge_id, transaction=t)
                except Exception as e:
                    db = self.mongo_client[os.environ["DB_NAME"]]
                    trans_col = db[os.environ["TRANSACTIONS"]]
                    await trans_col.update_one(
                        {"transactionId": t.transactionId},
                        {"$set": {"status": TransactionStatus.FAILED.value}}
                    )
                    logger.info(f"transaction : {t.transactionId} could not be included in the badge : {badge_id}")
            new_merkle_root = self.tree_controller.get_merkle_root()
            logger.info(new_merkle_root)

            blockhash, blocknumber, prev_id =  await self.get_previous_block_information()
            timestamp = get_current_timestamp()
            curr_block_hash = await self.create_block_hash(blocknumber=blocknumber +1,
            timestamp=timestamp, transactions=transaction_for_badge, previous_block_hash=blockhash)

            transaction_ids = [t.transactionId for t in transaction_for_badge]

            l2_badge_new = TransactionBadge(
                badgeId=badge_id,
                status=BadgeStatus.SEND_TO_VERIFY,
                blockhash=curr_block_hash,
                state_root=new_merkle_root,
                blocknumber=blocknumber + 1,
                timestamp=timestamp,
                executionCause=execution_cause,
                transactions=transaction_ids,
                prevBadge=prev_id
            )

            db = self.mongo_client[os.environ["DB_NAME"]]
            badges_col = db[os.environ["BADGES"]]
            await badges_col.insert_one(l2_badge_new.model_dump())
            logger.info({
                "state_root": new_merkle_root,
                "status" : BadgeStatus.SEND_TO_VERIFY.value,
                "timestamp" : timestamp,
                "blocknumber":  blocknumber +1,
                "blockhash" : curr_block_hash,
                "badgeId" : badge_id,
                "transactions" : [transaction_for_badge],
            })

        except Exception as e:
            logger.error(f"{e}")




    async def get_previous_block_information(self) -> tuple[str, int]:
        """
            Gets prev blockhash and blocknumber to increment
        """
        try:
            db = self.mongo_client[os.environ["DB_NAME"]]
            curr_col = db[os.environ["CURR"]]
            first_doc = await curr_col.find_one({})
            prev_badge_id = first_doc["currBadgeID"]
            badges_col = db[os.environ["BADGES"]]
            prev_badge = await badges_col.find_one({"badgeId": prev_badge_id})

            return [prev_badge["blockhash"], prev_badge["blocknumber"], prev_badge["badgeId"]]

        except Exception as e:
            logger.error(f"failed to retriece previous block information : {e}")



    
    async def create_block_hash(self, blocknumber: int, timestamp: int, transactions: list[Transaction], previous_block_hash: str) -> str:
        rolling_tx_hash: bytes = await self.create_rolling_transaction_hash(transactions=transactions)
        blocknumber_bytes = blocknumber.to_bytes(8, byteorder="big")
        timestamp_bytes = timestamp.to_bytes(8, byteorder="big")
        prev_block_hash_bytes = bytes.fromhex(previous_block_hash.replace("0x", ""))

        data = blocknumber_bytes + timestamp_bytes + prev_block_hash_bytes + rolling_tx_hash
        block_hash = hashlib.sha256(data).hexdigest()
        return "0x" + block_hash
        

    
    async def create_rolling_transaction_hash(self, transactions : list[Transaction]) -> bytes:
        if len(transactions) == 0:
            zero = 0
            return zero.to_bytes(8, byteorder="big")

        resulting_hash = None
        for t in transactions:
            if resulting_hash is None:
                zero = 0
                tx_hash = self.create_transaction_hash(t)
                zero_bytes = zero.to_bytes(8, byteorder="big")
                resulting_hash = hashlib.sha256(zero_bytes + tx_hash).digest()
            else:
                tx_hash = self.create_transaction_hash(t)
                resulting_hash = hashlib.sha256(resulting_hash + tx_hash)
        
        return resulting_hash



    def create_transaction_hash(self, t: Transaction) -> bytes:
        data = (
            t.sender.encode() +
            t.receiver.encode() +
            t.nonce.to_bytes(8, byteorder="big") +
            t.timestamp.to_bytes(8, byteorder="big") +
            t.signature.encode()
        )
        return hashlib.sha256(data).digest()
    
    async def badge_execution_task(self):
        logger.info("starting task")
        while True:
            await self.form_new_L2_block(BadgeExecutionCause.TIMEDOUT)
            await asyncio.sleep(10)
    
    async def create_transaction_flow(self):

        while True:
            trans =  await create_transaction()
            await self.mempool.insert_into_queue(trans, "1")
            await asyncio.sleep(1)
            












        

        
    
    

