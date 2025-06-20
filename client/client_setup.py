 

import json
import secrets
from nacl.signing import SigningKey
from MerkleTree import MerkleTree
import hashlib


NUM_ACCOUNTS = 8
BALANCE = 1000
JSON_PATH = "initial_account_state.json"

def generate_layer_2_funded_accounts():

    accounts = []
    for i in range(NUM_ACCOUNTS):
        # Generate a 32-byte seed and corresponding ed25519 keypair
        seed = secrets.token_hex(32)
        sk = SigningKey(bytes.fromhex(seed))
        vk = sk.verify_key

        account = {
            "priv_key": seed,                              # 64 hex chars
            "pub_key": vk.encode().hex(),                  # 64 hex chars
            "balance": BALANCE,
            "nonce": 0
        }
        accounts.append(account)
    return accounts

BATCH_SIZE = 8

def pack_balance_nonce(balance: int, nonce: int) -> bytes:
    return hashlib.sha256(balance.to_bytes(8, 'little') + nonce.to_bytes(8, 'little')).digest()

def data_to_byte_accounts(accounts : list[dict]) -> list[bytes]:
    leaves = []
    for acct in accounts:
        addr_bytes = bytes.fromhex(acct["pub_key"])
        bn_hash = pack_balance_nonce(acct['balance'], acct['nonce'])
        leaves.append(hashlib.sha256(addr_bytes + bn_hash).digest())
    return leaves

def generate_initial_state_root(accounts : list[object]):
    leaves = data_to_byte_accounts(accounts)
    merkle_tree = MerkleTree(leaves=leaves)
    initial_state = merkle_tree.root.hex()

    data = {
        "accounts" : accounts,
        "initial_state_root" : initial_state
    }

    with open(JSON_PATH, "w") as f:
        json.dump(data, f, indent=2)



if __name__ == "__main__":
    accounts = generate_layer_2_funded_accounts()
    generate_initial_state_root(accounts=accounts)



