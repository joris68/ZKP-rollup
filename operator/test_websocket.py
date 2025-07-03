from web3 import Web3
import sys
import logging
import json

CONTRACTS_JSON = "../broadcast/Deploy.s.sol/31337/run-latest.json"
NODE_ADDRESS = 'ws://127.0.0.1:8545'

def load_contract_address_and_name() -> dict:
    with open('YourContract.json') as f:
        contract_specs = json.load(f)['abi']
    return contract_specs

def load_abi():
    with open('HelloWorld.json') as f:
        abi = json.load(f)['abi']
    return abi


def _init_contract():
    info = load_contract_address_and_name()
    contract_address = info["address"]
    contract_name = info["name"]
    contract_abi = load_abi()
    return w3.eth.contract(address=contract_address, abi=contract_abi)

class ChainListener:

    def __init__(self):
        self.ws_conn = Web3(Web3.WebsocketProvider(NODE_ADDRESS))
        if not self.ws_conn.is_connected():
            logging.error("websocket connection failed")
            sys.exit(1)
    
    def load_contract_information(self) -> dict:
        with open('YourContract.json') as f:
            contract_abi = json.load(f)['abi']


class ChainCaller:

    def __init__(self):
        self.contract = self._init_contract()
    
    def _init_contract(self):
        info = load_contract_address_and_name()
        contract_address = info["address"]
        contract_name = info["name"]
        contract_abi = load_abi()
        return w3.eth.contract(address=contract_address, abi=contract_abi)



# Set up the event to watch
event_filter = contract.events.ValueChanged.create_filter(fromBlock='latest')

# Listen for events
print("Listening for ValueChanged events...")

try:
    while True:
        for event in event_filter.get_new_entries():
            print("\n🔔 New Event Received:")
            print(f"  From: {event['args']['author']}")
            print(f"  Old Value: {event['args']['oldValue']}")
            print(f"  New Value: {event['args']['newValue']}")
except KeyboardInterrupt:
    print("Stopped listening.")