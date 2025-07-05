from web3 import Web3
from eth_account import Account
import json


NODE_URL = "http://127.0.0.1:8545"
CONTRACT_ADDRESS = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"

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
    # Call the depositETH function (example, no arguments)
    tx = contract.functions.depositETH(address).build_transaction({
        "from": address,
        "value": web3.to_wei(1, "ether") # refers to the message value
    })
    print("Transaction:", tx)


if __name__ == "__main__": 
    address, piv_key = create_new_eht_account()
    make_deposit_call(address=address)
