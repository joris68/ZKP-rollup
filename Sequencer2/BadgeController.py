


from utils import get_current_timestamp
from MemPool import MemPool
import json
from Types import BadgeExecutionCause, Transaction, TransactionBadge
import hashlib
from collections import defaultdict
from typing import List, Dict
from AsyncMongoClient import get_mongo_client
import logging
from MerkleTreeController import MerkleTreeController

LEAF_DEFAULT_VALUE = "default"

#TODO dont forget to reset the badge

logger = logging.getLogger(__name__)

class BadgeController:

    def __init__(self):
        self.transaction_counter = 0
        self.last_timestamp = get_current_timestamp()
        self.mempool = MemPool()
        self.mongo_client = get_mongo_client()
        self.account_mapping = self.create_account_leaf_mapping()
        self.default_leaf_hash = self.hash_default_value()
        self.tree_controller = MerkleTreeController()
    
    
    async def form_new_L2_block(self, execution_cause : BadgeExecutionCause) -> TransactionBadge:


    
        transaction_for_badge = None
        if execution_cause == BadgeExecutionCause.FILLEDUP:
            transaction_for_badge = await self.mempool.get_transaction_for_badge()
        else:
            transaction_for_badge = await self.mempool.get_transaction_for_badge(last_timestamp=self.last_timestamp)
        
        for t in transaction_for_badge:
            # first update the sender
            key = hashlib.sha256(bytes.fromhex(t.receiver)).digest()
            value = "vql"
            self.sparse_merkle_tree.update()
            # then update the receiver

    async def summarize_change_log_for_badge(self):
        pass






        

        
    
    

