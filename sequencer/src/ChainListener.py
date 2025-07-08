from web3 import Web3
import sys
import logging
import json
import asyncio
import logging
from web3 import AsyncWeb3, AsyncHTTPProvider
from eth_abi.abi import decode
from src.MemPool import MemPool
from src.utils import get_current_timestamp

logger = logging.getLogger(__name__)



class ChainListener:

    def __init__(self, polling_interval : int, mempool : MemPool, node_addres : str, contract_address : str):
        try:
            self.NODE_ADDRESS = node_addres
            self.contract_address = contract_address
            self.contract = self._init_contract()
            if self.contract is None:
                raise RuntimeError("Contract initialization failed")
            self.polling_interval = polling_interval
            self.mempool = mempool
        except Exception as e:
            print(e)
            logger.error(f"Error occured in the system using : {e}")
            raise
    

    def load_abi(self):
        with open('Rollup.json') as f:
            abi = json.load(f)['abi']
        return abi
    
    def _init_contract(self):
        contract_abi = self.load_abi()
        w3 = AsyncWeb3(AsyncHTTPProvider(self.NODE_ADDRESS))
        checksum_address = Web3.to_checksum_address(self.contract_address)
        return w3.eth.contract(address=checksum_address, abi=contract_abi)
        
    async def _init_deposit_event_filter(self):
        return await self.contract.events.Deposit.create_filter(from_block='latest')

    async def _init_withdraw_event_filter(self):
        return await self.contract.events.Withdraw.create_filter(from_block='latest')
    
    async def handle_deposit_entries(self, deposit_entries):
        for dep in deposit_entries:
            logger.info("handling deposit event")
            deposit_args = dep['args']
            curr_time_stamp = get_current_timestamp()
            address = deposit_args["layer2Address"]
            amount = deposit_args["amount"]
            await self.mempool.insert_deposit_transaction(address=address, amount=amount, current_time_stamp=curr_time_stamp)

    async def deposit_chain_loop(self):
        deposit_event = await self._init_deposit_event_filter()
        while True:
            entries = await deposit_event.get_new_entries()
            await self.handle_deposit_entries(entries)
            await asyncio.sleep(self.polling_interval)


# if __name__ == "__main__":
#     listener = ChainListener(2, mempool=MemPool())
#     asyncio.run(listener.chain_loop())
