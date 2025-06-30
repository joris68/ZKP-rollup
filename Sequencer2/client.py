import json
import numpy as np
from nacl.signing import SigningKey
import hashlib
import requests
import time

JSON_PATH = "initial_account_state.json"

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
        msg = sender_bytes + receiver_bytes + nonce_bytes + amount_bytes
        return hashlib.sha256(msg).digest()
       

def create_transaction(sender : dict , receiver: dict, sender_idx : int) -> dict:
        trans_body = {
            "sender" : sender["pub_key"],
            "receiver" : receiver["pub_key"],
            "amount" : AMOUNT,
            "nonce": NONCES[sender_idx]
        }

        sk = SigningKey(bytes.fromhex(sender['priv_key']))
        msg = transaction_body_to_bytes(trans_body=trans_body)
        sig = sk.sign(msg).signature
        NONCES[sender_idx] += 1
        return {
               "signature" : sig.hex(),
               "body" : trans_body
        }

def create_and_send_transaction():
        a, b = choose_random_transaction_pair(state_data["accounts"])
        sender = state_data["accounts"][a]
        receiver = state_data["accounts"][b]
        data = create_transaction(sender, receiver, a)
        print(f"Transactionrequest: {json.dumps(data)}")
        response = requests.post(SEQUNCER_URL, json=data)
        print(response.status_code)
        print(response.json())
        


if __name__ == "__main__":
        while (True):
            create_and_send_transaction()
            time.sleep(1)
