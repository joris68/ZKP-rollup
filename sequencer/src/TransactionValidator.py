
from src.Types import Transaction
import logging
from src.utils import hex_to_bytes
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
                "amount": str(int(transaction.amount)),
                "nonce": transaction.nonce
            }
            message_json = json.dumps(tx_body, separators=(",", ":"), sort_keys=True)
            signature_bytes = hex_to_bytes(transaction.signature)
            pubkey_bytes = hex_to_bytes(transaction.pubKey)
            signature = keys.Signature(signature_bytes)
            public_key = keys.PublicKey(pubkey_bytes)
            message_bytes = message_json.encode("utf-8")
            return public_key.verify_msg(message_bytes, signature)

        except Exception as e:
            logger.info(e)
            return False
