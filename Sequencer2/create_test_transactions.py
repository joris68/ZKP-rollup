
import json
import numpy as np
import hashlib
from nacl.signing import SigningKey
from Types import Transaction

"""
    The: transaction schema:

    {
        "sender": "0x1f04204dba8e9e8bf90f5889fe4bdc0f37265dbb",
        "receiver": "0x05e3066450dfcd4ee9ca4f2039d58883631f0460",
        "amount": "12340000000000",
        "fee": "56700000000",
        "nonce": 784793056,
        "signature": {
            "pubKey": "0e1390d3e86881117979db2b37e40eaf46b6f8f38d2509ff3ecfaf229c717b9d",
            "signature": "817c866e71a0b3e6d412ac56524557d368c11332db93554693787e89c9813310adeda68314fc833a4f73323eca00e2cc774e78db88921dc230db7dae691fe500"
        }
    }
"""


JSON_PATH = "initial_state.json"

SEQUNCER_URL = "http://0.0.0.0:8000/api/submit"

AMOUNT = 1

NONCES = {i: 0 for i in range(9)}

with open(JSON_PATH, "r") as file:
        state_data = json.load(file)

def choose_random_transaction_pair(accounts: list[dict]) -> list[int]:
    indices = np.random.choice(len(accounts), size=2, replace=False)
    return indices.tolist()


def transaction_body_to_bytes(trans_body : dict) -> bytes:
        sender_bytes = bytes.fromhex(trans_body["sender"])
        receiver_bytes = bytes.fromhex(trans_body["receiver"])
        nonce_bytes = trans_body["nonce"].to_bytes(8, 'little') 
        amount_bytes = trans_body["amount"].to_bytes(8, 'little')
        fee_bytes = trans_body["fee"].to_bytes(8, 'little')
        msg = sender_bytes + receiver_bytes + nonce_bytes + amount_bytes + fee_bytes
        return hashlib.sha256(msg).digest()
       

def create_transaction(sender : dict , receiver: dict, sender_idx : int) -> dict:
        trans_body = {
            "sender" : sender["pub_key"],
            "receiver" : receiver["pub_key"],
            "amount" : AMOUNT,
            "nonce": NONCES[sender_idx],
            "fee" : 0.5
        }

        sk = SigningKey(bytes.fromhex(sender['priv_key']))
        msg = transaction_body_to_bytes(trans_body=trans_body)
        sig = sk.sign(msg).signature
        NONCES[sender_idx] += 1
        return {
            **trans_body ,
            "signature" :{
                "pubKey":   trans_body["sender"] ,
                "signature" : sig.hex()
            }
        }

async def create_transaction() -> Transaction:
        a, b = choose_random_transaction_pair(state_data["accounts"])
        sender = state_data["accounts"][a]
        receiver = state_data["accounts"][b]
        data = create_transaction(sender, receiver, a)
        return Transaction(**data)
        
        
