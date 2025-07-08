import uuid
import time
import hashlib
from src.Types import Transaction
import json
from eth_utils import keccak

def generate_random_id() -> str:
    return str(uuid.uuid4())
    
def get_current_timestamp() -> int:
    return int(time.time())


def create_message_from_transaction_body(body) -> bytes:
    trans_body = {
        "sender": body.sender,
        "receiver": body.receiver,
        "amount": str(body.amount),
        "nonce": body.nonce
    }
    message_json = json.dumps(trans_body, separators=(",", ":"), sort_keys=True)
    return keccak(text=message_json)

def hex_to_bytes(hex_str: str) -> bytes:
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]
    return bytes.fromhex(hex_str)

def bytes_to_hex(data: bytes) -> str:
    return "0x" + data.hex()

def add_0x_prefix(s: str) -> str:
    if not s.startswith("0x"):
        return "0x" + s
    return s