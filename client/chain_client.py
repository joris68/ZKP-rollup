from web3 import Web3
from eth_account import Account
import json


NODE_URL = "http://127.0.0.1:8545"
CONTRACT_ADDRESS = "0xe7f1725e7734ce288f8367e1bb143e90bb3f0512"

ACCOUNT_ADDRESS = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
ACCOUNT_PRIVATE_KEY = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"

def create_new_eht_account():
    Account.enable_unaudited_hdwallet_features()
    new_account = Account.create()
    print("Address:", new_account.address)
    print("Private Key:", new_account.key.hex())
    return new_account.address, new_account.key.hex()

def load_contract_abi() -> dict:
    with open("Rollup.json", "r") as f:
        contract_json = json.load(f)
    return contract_json["abi"]

def make_deposit_call(address):
    web3 = Web3(Web3.HTTPProvider(NODE_URL))
    contract_address = web3.to_checksum_address(CONTRACT_ADDRESS)
    contract_abi = load_contract_abi()
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)

    # Estimate gas
    gas_estimate = contract.functions.depositETH(address).estimate_gas({
        "from": address,
        "value": web3.to_wei(1, "ether")
    })

    gas_price = web3.eth.gas_price

    tx = contract.functions.depositETH(address).build_transaction({
        "from": address,
        "value": web3.to_wei(1, "ether"),
        "gas": gas_estimate,
        "gasPrice": gas_price,
        "nonce": web3.eth.get_transaction_count(address)
    })
    print("Transaction:", tx)
     # Sign the transaction
    signed_tx = web3.eth.account.sign_transaction(tx, private_key=ACCOUNT_PRIVATE_KEY)

    # Send the transaction
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print("Transaction hash:", tx_hash.hex())

    # (Optional) Wait for receipt
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    print("Transaction receipt:", receipt)


if __name__ == "__main__": 
    make_deposit_call(address=ACCOUNT_ADDRESS)
