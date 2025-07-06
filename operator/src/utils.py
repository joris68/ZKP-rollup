import uuid
import time
import hashlib
from operator.src.Types import Transaction

def generate_random_id() -> str:
    return str(uuid.uuid4())
    
def get_current_timestamp() -> int:
    return int(time.time())

def create_message_from_transaction_body( body : Transaction) -> bytes:
        sender_bytes = bytes.fromhex(body.sender)
        receiver_bytes = bytes.fromhex(body.receiver)
        nonce_bytes = body.nonce.to_bytes(8, 'little')
        amount_bytes = int(body.amount).to_bytes(8, 'little')
        msg = sender_bytes + receiver_bytes + nonce_bytes + amount_bytes
        return hashlib.sha256(msg).digest()