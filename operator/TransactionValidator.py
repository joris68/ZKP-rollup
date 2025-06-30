
from Types import Transaction
import os
import logging
from nacl.signing import VerifyKey
import hashlib
import struct
from utils import create_message_from_transaction_body

logger = logging.getLogger(__name__)

class Transaction_Validator(object):


    async def check_transaction_validity(self, transaction : Transaction, submission_id : str) -> bool:
        logger.info("starting to check the transaction validity")
        dig_signature = transaction.signature
        sig_binary = bytes.fromhex(dig_signature)
        sender_address = transaction.sender
        vk = VerifyKey(bytes.fromhex(sender_address))
        msg = create_message_from_transaction_body(transaction)
        try:
            vk.verify(msg,sig_binary)
            logger.info(f"signature of {submission_id} valid")
            return True
        except:
            logger.info(f"Signature of {submission_id} not valid due to invalid signature")
            return False



