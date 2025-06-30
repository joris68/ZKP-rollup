from utils import get_current_timestamp
from MemPool import MemPool
from Types import BadgeExecutionCause, TransactionBadge, TransactionStatus, BadgeStatus, Transaction, TransactionRequest
from AsyncMongoClient import get_mongo_client
import logging
from MerkleTreeController import MerkleTreeController
from utils import generate_random_id, create_message_from_transaction_body
import os
import hashlib
import asyncio
from create_test_transactions import create_transaction_to_submit


logger = logging.getLogger(__name__)

"""
    Blocknumber increments monotonically
    Blockhash is determined by the : H(bocknumber, _blocktimestamp, _prevL2BlockHash, _blockTxsRollingHash)
    Tx rolling hash: H(H(0, t_1), t_2) ....
"""

class BadgeController:

    def __init__(self):
        self.transaction_counter = 0
        self.last_timestamp = get_current_timestamp()
        self.mempool = MemPool()
        self.mongo_client = get_mongo_client()
        self.tree_controller = MerkleTreeController()
    

    async def _get_transaction_for_badge(self, badge_execution_cause : BadgeExecutionCause) -> list[Transaction]:
        transaction_for_badge = None
        if badge_execution_cause == BadgeExecutionCause.FILLEDUP:
            transaction_for_badge = await self.mempool.get_transaction_for_badge()
        else:
            transaction_for_badge = await self.mempool.get_transaction_for_badge(last_timestamp=self.last_timestamp)
        return transaction_for_badge


    async def _update_merkle_tree(self, badged_transaction : list[Transaction], badge_id : str) -> list[Transaction]:
            db = self.mongo_client[os.environ["DB_NAME"]]
            trans_col = db[os.environ["TRANSACTIONS"]]
            failed_transaction = []
            for t in badged_transaction:
                try:
                    await self.tree_controller.make_rollup_transaction_between_existing_users(badge_id=badge_id, transaction=t)
                except Exception as e:
                    await trans_col.update_one(
                        {"transactionId": t.transactionId},
                        {"$set": {"status": TransactionStatus.FAILED.value}}
                    )
                    logger.error(f"{e}")
                    failed_transaction.append(t.transactionId)
                    logger.info(f"transaction : {t.transactionId} could not be included in the badge : {badge_id}")
            
            return [t for t in badged_transaction if t.transactionId not in failed_transaction]
    
    async def increment_badge_pointer(self, next_badge_id : str) -> None:
        try:
            db = self.mongo_client[os.environ["DB_NAME"]]
            badge_col = db[os.environ["CURR"]]
            await badge_col.update_one(
                {},
                {"$set": {"currBadgeID": next_badge_id}}
            )
            logger.info("badge pointer got incremented")
        except Exception as e:
            logger.error(f"cannot increment the badgepointer: {e}")
    
    async def insert_new_badge(self , badge : TransactionBadge, next_badge_id : str) -> None:
        try:
            db = self.mongo_client[os.environ["DB_NAME"]]
            badges_col = db[os.environ["BADGES"]]
            await badges_col.insert_one(badge.model_dump())
            await self.increment_badge_pointer(next_badge_id=next_badge_id)
        except Exception as e:
            logger.error(f"error when updating the badge pointer: {e}")
    
    
    async def form_new_L2_block(self, execution_cause : BadgeExecutionCause) -> TransactionBadge:
        logger.info("starting to form new L2 block ")
        try:
            badge_id = generate_random_id()
        
            badged_transaction = await self._get_transaction_for_badge(badge_execution_cause=execution_cause)
            self.last_timestamp = get_current_timestamp()
            logger.info(f"retrived : {len(badged_transaction)} transaction for badge : {badge_id}")
            old_merkle_root = self.tree_controller.get_merkle_root()
            transactions_for_delta = await self._update_merkle_tree(badged_transaction=badged_transaction, badge_id=badge_id)
            new_merkle_root = self.tree_controller.get_merkle_root()
            logger.info(new_merkle_root)
            blockhash, blocknumber, prev_id =  await self.get_previous_block_information()
            timestamp = get_current_timestamp()
            curr_block_hash = await self.create_block_hash(blocknumber=blocknumber +1,
            timestamp=timestamp, transactions=badged_transaction, previous_block_hash=blockhash)
            
            #here send badge to ZK
            logger.info({
                "new_state_root": new_merkle_root,
                "old_state_root" : old_merkle_root,
                "timestamp" : timestamp,
                "blocknumber":  blocknumber +1,
                "blockhash" : curr_block_hash,
                "badgeId" : badge_id,
                "transactions" : transactions_for_delta,
            })

            transaction_ids = [t.transactionId for t in transactions_for_delta]

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
            await self.insert_new_badge(badge=l2_badge_new, next_badge_id=badge_id)

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
            a = [prev_badge["blockhash"], prev_badge["blocknumber"], prev_badge["badgeId"]]
            logger.info(a)
            return a

        except Exception as e:
            logger.error(f"failed to retriece previous block information : {e}")



    
    async def create_block_hash(self, blocknumber: int, timestamp: int, transactions: list[Transaction], previous_block_hash: str) -> str:
        logger.info(f"prev block hash : {previous_block_hash}")
        try: 
            rolling_tx_hash: bytes = await self.create_rolling_transaction_hash(transactions=transactions)
            blocknumber_bytes = blocknumber.to_bytes(8, 'little')
            timestamp_bytes = timestamp.to_bytes(8, 'little')
            prev_block_hash_bytes = bytes.fromhex(previous_block_hash)
            data = blocknumber_bytes + timestamp_bytes + prev_block_hash_bytes + rolling_tx_hash
            return hashlib.sha256(data).hexdigest()
        except Exception as e:
            logger.info(f"error in create blockhash : {e}")
        

    
    async def create_rolling_transaction_hash(self, transactions : list[Transaction]) -> bytes:
        if len(transactions) == 0:
            zero = 0
            return zero.to_bytes(8, 'little')

        resulting_hash = None
        for t in transactions:
            if resulting_hash is None:
                zero = 0
                tx_hash = self.create_transaction_hash(t)
                zero_bytes = zero.to_bytes(8, 'little')
                resulting_hash = hashlib.sha256(zero_bytes + tx_hash).digest()
            else:
                tx_hash = self.create_transaction_hash(t)
                resulting_hash = hashlib.sha256(resulting_hash + tx_hash).digest()
        
        return resulting_hash


    def create_transaction_hash(self, t: Transaction) -> bytes:
        sender_bytes = bytes.fromhex(t.sender)
        receiver_bytes = bytes.fromhex(t.receiver)
        nonce_bytes = t.nonce.to_bytes(8, 'little')
        amount_bytes = int(t.amount).to_bytes(8, 'little')
        received_bytes = t.receivedAt.to_bytes(8, 'little')
        msg = sender_bytes + receiver_bytes + nonce_bytes + amount_bytes + received_bytes
        return hashlib.sha256(msg).digest()
    
    def enrich_transaction(self, transaction_request: TransactionRequest, submission_id : str) -> Transaction:
        return Transaction(
            receivedAt= get_current_timestamp(),
            submissionId=submission_id,
            transactionId= generate_random_id(),
            sender=transaction_request.sender,
            receiver=transaction_request.receiver,
            nonce=transaction_request.nonce,
            signature=transaction_request.signature.signature,  # Extract the signature string
            amount=transaction_request.amount,
            status=TransactionStatus.PENDING,
            badgeId = None
        )
    
    async def badge_execution_task(self):
        logger.info("starting task")
        while True:
            await self.form_new_L2_block(BadgeExecutionCause.TIMEDOUT)
            await asyncio.sleep(10)
    
    async def create_transaction_flow(self):
        while True:
            try:
                trans_req = await create_transaction_to_submit()
                submission_id = generate_random_id()
                trans = self.enrich_transaction(transaction_request=trans_req, submission_id=submission_id)
                await self.mempool.insert_into_queue(trans, submisson_id=submission_id)
                logger.info("Inserted transaction into mempool")
            except Exception as e:
                logger.error(f"Error in create_transaction_flow: {e}")
            await asyncio.sleep(1)



















