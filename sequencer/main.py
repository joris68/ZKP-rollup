import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import logging
import json
from dotenv import load_dotenv
from src.BlockController import BlockController
from src.Types import TransactionRequest, SubmissionResponse, NonceResponse, SubmissionStatus, NonceRequest, SubmissionStatusRequest
from src.SetupService import SetupService
import asyncio
from src.ChainListener import ChainListener

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
load_dotenv()

NODE_ADDRESS = 'http://127.0.0.1:8545'
CONTRACT_ADDRESS = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"

queue = asyncio.Queue()
setup_service = SetupService(start_users_needed=True)
badge_controller = BlockController(queue=queue, with_account_setup=True)
chain_listener = ChainListener(polling_interval=2, mempool=badge_controller.mempool, node_addres=NODE_ADDRESS, contract_address=CONTRACT_ADDRESS)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await setup_service.on_start()
    loop = asyncio.get_running_loop()
    loop.create_task(badge_controller.batch_queue_producer())
    loop.create_task(badge_controller.batch_queue_consumer())
    loop.create_task(chain_listener.deposit_chain_loop())
    logger.info("setup complete")
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/api/submit")
async def submit_transaction(transaction: TransactionRequest) -> SubmissionResponse:
    try:
        return await badge_controller.handel_transaction_submission(transaction_request=transaction)
    except Exception as e :
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"{e}")

@app.post("/api/get-nonce")
async def get_nonce_for_account(req : NonceRequest) -> NonceResponse:
    try:
        return await badge_controller.get_nonce_for_account(account=req.account)
    except Exception as e :
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/get-status")
async def get_status_from_transaction(req : SubmissionStatusRequest) -> SubmissionResponse:
    try:
        return await badge_controller.get_status_for_transaction(submission_id=req.submission_id)
    except Exception as e :
        raise HTTPException(status_code=500, detail="Internal server error")
       

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)