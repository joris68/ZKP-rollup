
from src.Types import Transaction
import os
import logging
from nacl.signing import VerifyKey
import hashlib
import struct
from src.utils import create_message_from_transaction_body, hex_to_bytes
import json
from eth_utils import keccak, to_bytes
from eth_keys import keys

logger = logging.getLogger(__name__)

class Transaction_Validator(object):
    
    async def check_transaction_validity(self, transaction : Transaction, submission_id : str) -> bool:
        logger.info("starting to check the transaction validity")
        try:
            tx_body = {
                "sender" : transaction.sender,
                "receiver" : transaction.receiver,
                "amount": str(transaction.amount),
                "nonce": transaction.nonce
            }
            message_json = json.dumps(tx_body, separators=(",", ":"), sort_keys=True)
            message_hash = keccak(text=message_json)
            signature_bytes = to_bytes(transaction.signature)
            pubkey_bytes = to_bytes(transaction.pubKey)
            signature = keys.Signature(signature_bytes)
            public_key = keys.PublicKey(pubkey_bytes)
            return public_key.verify_msg_hash(message_hash, signature)

        except Exception as e:
            logger.info(e)
            return False



