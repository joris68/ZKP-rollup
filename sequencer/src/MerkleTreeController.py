
from src.Types import Transaction, AccountsCollection
import json
import hashlib
from smt.tree import SparseMerkleTree
from  src.AsyncMongoClient import get_mongo_client
import os
import logging
from src.utils import hex_to_bytes, bytes_to_hex

logger = logging.getLogger(__name__)

class MerkleTreeController:

    def __init__(self, with_account_setup : bool):
        if with_account_setup:
            self.sparse_merkle_tree = self.initilize_sparse_merkle_tree()
        else:
            self.sparse_merkle_tree = SparseMerkleTree()
        self.mongo_client = get_mongo_client()

    
    async def make_rollup_transaction_between_existing_users(self, badge_id : str, transaction : Transaction) -> None:
        """
            Implements the rollup Operation: Transfer funds between Existing rollup accounts
        """
        invariants_succeded = await self._check_tree_invariants_for_update(transaction=transaction)
        if not invariants_succeded:
            logger.info(f"in badge : {badge_id} and transaction: {transaction.transactionId} did not pass the invariants")
            logger.error("invariants problem: tree invariants failed")
            raise Exception("Tree invariants failed")
        try:
            new_sender_leaf_data = await self.update_sender_leaf_return_bytes(badge_id=badge_id, transaction=transaction)
            self.sparse_merkle_tree.update(hex_to_bytes(transaction.sender), new_sender_leaf_data)
            new_receiver_leaf = await self.update_receiver_bytes_return_bytes(badge_id=badge_id, transaction=transaction)
            self.sparse_merkle_tree.update(hex_to_bytes(transaction.receiver), new_receiver_leaf)
        except Exception as e:
            logger.error(f"Error when updating leaf data : {e}")
            raise e
    
    async def handle_deposit_transaction(self, badge_id : str, transaction : Transaction) -> None:
        try:
            new_leaf_data= await self.leaf_to_bytes(balance=transaction.amount, nonce=0, account=transaction.sender)
            logger.info(new_leaf_data)
            logger.info(type(new_leaf_data))
            self.sparse_merkle_tree.update(hex_to_bytes(transaction.sender), new_leaf_data)
        except Exception as e :
            logger.error(f"Error when inserting deposit into the tree: {e}")
            raise e


    def get_merkle_root(self) -> str:
        return self.sparse_merkle_tree.root_as_hex()

    
    async def update_sender_leaf_return_bytes(self, badge_id : str, transaction : Transaction) -> bytes:
        async with await self.mongo_client.start_session(causal_consistency=True) as session:
                try:
                    logger.info(f"updating sender leaf data for change log")
                    db = self.mongo_client[os.environ["DB_NAME"]]
                    users_col = db[os.environ["USERS"]]
                    prev_sender = await users_col.find_one({
                         "address": transaction.sender,
                    })
                    account_updates = prev_sender.get("account_updates", [])
                    update_index = None
                    for acc in range(0, len(account_updates)):
                        if account_updates[acc].get(("badgeId") == badge_id):
                            update_index = acc

                    if update_index is not None:
                        new_balance = prev_sender.account_updates[update_index] - transaction.amount
                        new_nonce = prev_sender.account_updates[update_index]["nonce_before"] + 1
                        await users_col.update_one(
                                {
                                    "address": transaction.sender,
                                    "account_updates.badgeId": badge_id
                                },
                                {
                                    "$set": {
                                        "account_updates.$.balance_after": new_balance,
                                        "account_updates.$.nonce_after": new_nonce
                                    },
                                    "$push": {
                                        "account_updates.$.transactions": transaction.transactionId
                                    }
                                },
                                session=session
                            )
                        new_leaf_bytes =  await self.leaf_to_bytes(new_balance, new_nonce, account=transaction.sender)
                        return new_leaf_bytes
                    else:
                            balance_before = None
                            nonce_before = None
                            if len(account_updates) == 0:
                                balance_before = prev_sender["balance"]
                                nonce_before = prev_sender["nonce"]
                            else :
                                last_sub = prev_sender["account_updates"][len(account_updates) -2]
                                balance_before = last_sub["balance_after"]
                                nonce_before = last_sub["nonce_after"]
                            
                            new_balance = balance_before - transaction.amount #+ transaction.fee)
                            new_nonce = nonce_before + 1

                            await users_col.update_one(
                                {"address": transaction.sender},
                                {
                                    "$push": {
                                        "account_updates": {
                                            "balance_before": balance_before,
                                            "balance_after": new_balance,
                                            "nonce_before": nonce_before,
                                            "nonce_after": new_nonce,
                                            "transactions": [transaction.transactionId],
                                            "badgeId": badge_id
                                        }
                                    }
                                },
                                session=session
                            )
                            new_leaf_bytes = await self.leaf_to_bytes(new_balance, new_nonce, account= transaction.sender)
                            return new_leaf_bytes
                except Exception as e:
                    logger.error(f"error in updating the chnagelog for transaction : {transaction.transactionId}")
                    logger.error(f"{e}")
                    raise e
    
    async def update_receiver_bytes_return_bytes(self, badge_id : str, transaction : Transaction) -> bytes:
         """
            receiver nonces do not get updated
         """
         async with await self.mongo_client.start_session(causal_consistency=True) as session:
                try:
                    logger.info(f"updating receiver leaf data for change log")
                    db = self.mongo_client[os.environ["DB_NAME"]]
                    users_col = db[os.environ["USERS"]]
                    prev_receiver = await users_col.find_one({
                         "address": transaction.receiver,
                    })
                    account_updates = prev_receiver.get("account_updates", [])
                    update_index = None
                    for acc in range(0, len(account_updates)):
                        if account_updates[acc].get(("badgeId") == badge_id):
                            update_index = acc

                    if update_index is not None:
                        new_balance = prev_receiver.account_updates[update_index] + transaction.amount
                        new_nonce = prev_receiver.account_updates[update_index]["nonce_after"]
                        await users_col.update_one(
                                {
                                    "address": transaction.receiver,
                                    "account_updates.badgeId": badge_id
                                },
                                {
                                    "$set": {
                                        "account_updates.$.balance_after": new_balance,
                                        "account_updates.$.nonce_after": new_nonce
                                    },
                                    "$push": {
                                        "account_updates.$.transactions": transaction.transactionId
                                    }
                                },
                                session=session
                            )
                        new_leaf_bytes = await self.leaf_to_bytes(new_balance, new_nonce, account=transaction.receiver)
                        return new_leaf_bytes
                    else:
                            balance_before = None
                            nonce_before = None
                            if len(account_updates) == 0:
                                balance_before = prev_receiver["balance"]
                                nonce_before = prev_receiver["nonce"]
                            else :
                                last_sub = prev_receiver["account_updates"][len(account_updates) -1]
                                balance_before = last_sub["balance_after"]
                                nonce_before = last_sub["nonce_after"]
                            
                            new_balance = balance_before + transaction.amount
                            new_nonce = nonce_before

                            await users_col.update_one(
                                {"address": transaction.sender},
                                {
                                    "$push": {
                                        "account_updates": {
                                            "balance_before": balance_before,
                                            "balance_after": new_balance,
                                            "nonce_before": nonce_before,
                                            "nonce_after": new_nonce,
                                            "transactions": [transaction.transactionId],
                                            "badgeId": badge_id
                                        }
                                    }
                                },
                                session=session
                            )

                            new_leaf_bytes =  await self.leaf_to_bytes(new_balance, new_nonce, account= transaction.receiver)
                            return new_leaf_bytes
                except Exception as e:
                    logger.error(f"error in updating the chnagelog for transaction : {transaction.transactionId}")
                    raise e

    async def leaf_to_bytes(self, balance : int, nonce : int , account : str ) -> bytes:

        nonce_bytes = int(nonce).to_bytes(8, 'little') 
        balance_bytes = int(balance).to_bytes(8, 'little')
        hashes_pub = hex_to_bytes(account)
        msg = balance_bytes + nonce_bytes + hashes_pub
        return msg
        
    
    async def _check_tree_invariants_for_update(self, transaction : Transaction) -> bool:
         async with await self.mongo_client.start_session(causal_consistency=True) as session:
                try:
                    db = self.mongo_client[os.environ["DB_NAME"]]
                    users_col = db[os.environ["USERS"]]
                    account  = await users_col.find_one({"address" : transaction.sender}, session=session)
                    if account is None:
                        logger.error(f"account data could not be found when quering for it")
                        return False
                    account_object = AccountsCollection(**account)
                    balance_sufficient = account_object.balance >= transaction.amount #+ fee
                    if len(account_object.account_updates) > 0:
                        latest_nonce = account_object.account_updates[-1].nonce_after
                        latest_balance = account_object.account_updates[-1].balance_after
                    else:
                        latest_nonce = account_object.nonce
                        latest_balance = account_object.balance

                    balance_sufficient = latest_balance >= transaction.amount
                    nonce_correct = latest_nonce == transaction.nonce
                    account_receiver  = await users_col.find_one({"address" : transaction.receiver}, session=session)

                    endresult = (balance_sufficient and  nonce_correct and (account_receiver is not None))
                    logger.info(f"endresult of the tree invariants : {endresult}")
                    return endresult

                except Exception as e:
                    logger.info(f"{e}")
                    return False
    

    def initilize_sparse_merkle_tree(self) -> SparseMerkleTree:
        logger.info("starting to initialize sparse merkle tree")
        with open("funded_accounts.json", "r") as file:
            users_data = json.load(file)
        
        tree = SparseMerkleTree()

        for acc in users_data:
            key = hex_to_bytes(acc["pub_key"])
            value = self.hash_account_to_leaf_value(account_data= acc)
            tree.update(key = key, value = value)
        
        logger.info("done inserting leaf values")
        return tree
    
    def hash_account_to_leaf_value(self, account_data) -> bytes:
        balance = account_data["balance"]
        nonce = 0
        pub_key = account_data["pub_key"]

        nonce_bytes = int(nonce).to_bytes(8, 'little') 
        balance_bytes = int(balance).to_bytes(8, 'little')

        hashes_pub = hex_to_bytes(pub_key)
        msg = balance_bytes + nonce_bytes + hashes_pub
        return msg
        
