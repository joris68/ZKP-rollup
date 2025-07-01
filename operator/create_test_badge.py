import logging
from create_test_transactions import create_transaction_to_submit
import asyncio
from smt.tree import SparseMerkleTree
import hashlib
import json

tree = SparseMerkleTree()

accounts = [
    {
    "pub_key": "f19967f9a95037329e7dba14f6561352c2d726555f6f93c697eac9e0c2296fa8",
    "balance": 1000,
    "nonce": 0,
    },
    {
    "pub_key": '0bda2f5dd27480bc0cde47acf20a231762d9b68d9571993322e3981fe86f279d',
    "balance": 1000,
    "nonce": 0,
    }
]

transactions = [{
    "from" : "f19967f9a95037329e7dba14f6561352c2d726555f6f93c697eac9e0c2296fa8",
    "to" : "0bda2f5dd27480bc0cde47acf20a231762d9b68d9571993322e3981fe86f279d",
    "nonce" : 0,
    "amount" : 1
}]

def leaf_to_bytes( balance : int, nonce : int , pub_key : str ) -> bytes:

    nonce_bytes = int(nonce).to_bytes(8, 'little') 
    balance_bytes = int(balance).to_bytes(8, 'little')
    hashes_pub = bytes.fromhex(pub_key)
    msg = balance_bytes + nonce_bytes + hashes_pub
    return msg

def get_start_root() -> str:
    for acc in accounts:
        bytes_key = bytes.fromhex(acc["pub_key"])
        bytes_leaf = leaf_to_bytes(acc["balance"], acc["nonce"], acc["pub_key"])
        tree.update(key = bytes_key , value = bytes_leaf)
    
    return tree.root_as_hex()

def proof_to_json(proof) -> dict:
    return {
        "sidenodes": [s.hex() for s in proof.sidenodes],
        "non_membership_leafdata": proof.non_membership_leafdata.hex() if proof.non_membership_leafdata else None,
        "sibling_data": proof.sibling_data.hex() if proof.sibling_data else None,
    }



def get_merkle_proofs():
    proofs = []
    for acc in accounts:
        bytes_key = bytes.fromhex(acc["pub_key"])
        proof = tree.prove(bytes_key)
        proofs.append(proof)
    
    return proofs


if __name__ == "__main__":
    start_root = get_start_root()
    print(start_root)
    proofs = get_merkle_proofs()
    badge = {
        "old_merkle_root" : start_root,
        "leaf_data" : accounts,
        "transactions" : transactions,
        "inclusion_proof" : [proof_to_json(proof) for proof in proofs],
        "badgeId" : 1
    }
    print(badge)
    # Write badge to test_badge.json
    with open("test_badge.json", "w") as f:
        json.dump(badge, f, indent=2)







