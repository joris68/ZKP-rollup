from eth_keys import keys
import json
import hashlib

def verify_transaction_signature(tx: dict) -> bool:
    body = {
        "from": tx["from"],
        "to": tx["to"],
        "amount": tx["amount"],
        "nonce": tx["nonce"]
    }
    serialized = json.dumps(body, sort_keys=True, separators=(',', ':'))
    tx_hash = hashlib.sha256(serialized.encode('utf-8')).digest()

    pub_key_hex = tx["signature"]["pubKey"]
    signature_hex = tx["signature"]["signature"]

    if pub_key_hex.startswith("0x"):
        pub_key_hex = pub_key_hex[2:]
    if signature_hex.startswith("0x"):
        signature_hex = signature_hex[2:]

    pub_key = keys.PublicKey(bytes.fromhex(pub_key_hex))
    signature = keys.Signature(bytes.fromhex(signature_hex))

    return pub_key.verify_msg_hash(tx_hash, signature)

def verify_all_signatures(json_file_path: str) -> bool:
    with open(json_file_path, "r") as f:
        data = json.load(f)
    all_valid = True
    for tx in data["transactions"]:
        valid = verify_transaction_signature(tx)
        print(f"Tx from {tx['from']} to {tx['to']} valid: {valid}")
        if not valid:
            all_valid = False
    return all_valid

# Example usage:
result = verify_all_signatures("badge_30_20.json")
print("All signatures valid:", result)