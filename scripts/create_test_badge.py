
from smt.tree import SparseMerkleTree
from eth_account import Account
import secrets
from eth_keys import keys
import numpy as np
import hashlib
import json
import uuid

def create_account_information(num: int) -> list[dict]:
    accounts = []
    for _ in range(0, num):
        private_key_bytes = secrets.token_bytes(32)
        private_key = keys.PrivateKey(private_key_bytes)
        pub = private_key.public_key
        accounts.append({
            "private_key": bytes_to_hex(private_key_bytes),
            "public_key": pub.to_hex(),
            "balance": 1000,
            "nonce": 0
        })
    return accounts

def choose_random_transaction_pair(number_accounts: int) -> list[int]:
    indices = np.random.choice(number_accounts, size=2, replace=False)
    return indices.tolist()

def hex_to_bytes(hex_str: str) -> bytes:
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]
    return bytes.fromhex(hex_str)

def bytes_to_hex(data: bytes) -> str:
    return "0x" + data.hex()

def leaf_data_to_bytes( balance : int, nonce : int , pub_key : str ) -> bytes:
    nonce_bytes = int(nonce).to_bytes(8, 'little') 
    balance_bytes = int(balance).to_bytes(8, 'little')
    pub_key_bytes = hex_to_bytes(pub_key)
    msg = balance_bytes + nonce_bytes + pub_key_bytes
    return msg

def apply_transaction(transaction : dict, account_information : list[dict], tree : SparseMerkleTree, participients : list[int] ):
    # update account info
    account_information[participients[0]]["balance"] -= transaction["amount"]
    account_information [participients[0]]["nonce"] +=1
    account_information[participients[1]]["balance"] += transaction["amount"]

    # update tree:
    balance_from = account_information[participients[0]]["balance"]
    nonce_from = account_information[participients[0]]["nonce"]
    pub_key_from = account_information[participients[0]]["public_key"]
    new_from_leaf_data = leaf_data_to_bytes(balance=balance_from, nonce=nonce_from, pub_key=pub_key_from)
    tree.update(hex_to_bytes(pub_key_from), new_from_leaf_data)

    balance_to = account_information[participients[1]]["balance"]
    nonce_to = account_information[participients[1]]["nonce"]
    pub_key_to = account_information[participients[1]]["public_key"]
    new_to_leaf_data = leaf_data_to_bytes(balance=balance_to, nonce=nonce_to, pub_key=pub_key_to)
    tree.update(hex_to_bytes(pub_key_to), new_to_leaf_data)


def create_transaction(account_information : list[dict] , participients : list[int]):
    from_acc = account_information[participients[0]]
    to_acc = account_information[participients[1]]
    body =  {
        "from": from_acc["public_key"],
        "to" : to_acc["public_key"],
        "amount":  1,
        "nonce":  from_acc["nonce"]
    }
    serialized = json.dumps(body, sort_keys=True, separators=(',', ':'))
    tx_hash = hashlib.sha256(serialized.encode('utf-8')).digest()
    private_key = keys.PrivateKey(hex_to_bytes(from_acc["private_key"]))
    signature = private_key.sign_msg_hash(tx_hash)

    return {
        **body,
        "signature" : {
            "pubKey": from_acc["public_key"],
            "signature": bytes_to_hex(signature.to_bytes())
        }
    }



def initialize_merkle_tree(account_information : list[dict], tree : SparseMerkleTree) -> str:
    for acc in account_information:
        bytes_key = hex_to_bytes(acc["public_key"])
        bytes_leaf = leaf_data_to_bytes(acc["balance"], acc["nonce"], acc["public_key"])
        tree.update(key = bytes_key , value = bytes_leaf)
    
    return tree.root_as_hex()

def proof_to_json(proof) -> dict:
    return {
        "sidenodes": [bytes_to_hex(s) for s in proof.sidenodes],
        "non_membership_leafdata": proof.non_membership_leafdata.hex() if proof.non_membership_leafdata else None,
        "sibling_data": proof.sibling_data.hex() if proof.sibling_data else None,
    }


def view_on_account_information(account_information: list[dict]) -> list[dict]:
    views = []
    for acc in account_information:
        view = {
            "public_key": acc["public_key"],
            "balance": acc["balance"],
            "nonce": acc["nonce"]
        }
        views.append(view)
    
    return views


def get_merkle_proofs(sending_pairs : list[list[int]], tree : SparseMerkleTree, account_information : list[dict]) -> list[dict]:
    unique_sender = {pair[0] for pair in sending_pairs}
    inclusion_proofs = []
    for sender in unique_sender:
        key_str = account_information[sender]["public_key"]
        prove = tree.prove(hex_to_bytes(key_str))
        inclusion_proofs.append(proof_to_json(proof=prove))
    
    return inclusion_proofs



def main(amount_transactions : int, amount_leafs : int, file_name : str):
    tree = SparseMerkleTree()
    account_information = create_account_information(amount_leafs)
    start_root = initialize_merkle_tree(account_information=account_information, tree=tree)
    sending_pairs = []
    transactions = []
    for x in range(0, amount_transactions):
        participients = choose_random_transaction_pair(len(account_information))
        sending_pairs.append(participients)
        transaction = create_transaction(account_information=account_information, participients=participients)
        transactions.append(transaction)
        apply_transaction(transaction=transaction, account_information=account_information, tree=tree, participients=participients)
    
    leaf_data = view_on_account_information(account_information=account_information)
    inclusion_proofs = get_merkle_proofs(sending_pairs=sending_pairs, tree=tree, account_information=account_information)
    badge_id = 1
    badge = {
        "old_merkle_root": start_root,
        "leaf_data" : leaf_data,
        "transactions" : transactions,
        "inclusion_proofs" : inclusion_proofs,
        "badge_id" : badge_id
    }
    with open(file_name, "w") as f:
        json.dump(badge, f, indent=2)


if __name__ == "__main__":
    main(amount_transactions=30, amount_leafs=20, file_name="badge_30_20.json")







