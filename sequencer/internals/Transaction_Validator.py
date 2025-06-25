from internals.Mongo_client import get_mongo_client
from Pydantic_Types import TransactionRequest, TransactionBody, UsersCollection
import os
import logging
from nacl.signing import VerifyKey
import hashlib

logger = logging.getLogger(__name__)

class Transaction_Validator(object):

    def __init__(self):
        self.mongo = get_mongo_client()


    async def check_transaction_validity(self, transactionReq : TransactionRequest, submission_id : str) -> bool:
        logger.info("starting to check the transaction validity")
        dig_signature = transactionReq.signature
        sig_binary = bytes.fromhex(dig_signature)
        sender_address = transactionReq.body.sender
        vk = VerifyKey(bytes.fromhex(sender_address))
        msg = self._create_message_from_transaction_body(transactionReq.body)
        try:
            vk.verify(msg,sig_binary)
            logger.info(f"signature of {submission_id} valid")
        except:
            logger.info("transaction is not valid due to invalid digital signature")
            return False

        user_col = self.mongo[os.environ["USERS"]]
        user : UsersCollection = user_col.find_one({"address" : sender_address})
        logger.info(user["latestNonce"])
        logger.info(transactionReq.body.nonce - 1)
        if user["latestNonce"] != transactionReq.body.nonce - 1:
            logger.info("Transaction rejected due to invalid nonce provided")
            return False
        return True


    def _create_message_from_transaction_body(self, body : TransactionBody) -> bytes:
        sender_bytes = bytes.fromhex(body.sender)
        receiver_bytes = bytes.fromhex(body.receiver)
        nonce_bytes = body.nonce.to_bytes(8, 'little') 
        amount_bytes = body.amount.to_bytes(8, 'little')
        msg = sender_bytes + receiver_bytes + nonce_bytes + amount_bytes
        return hashlib.sha256(msg).digest()




    
        