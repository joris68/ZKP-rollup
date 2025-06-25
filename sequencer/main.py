import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
import logging
import json
from dotenv import load_dotenv
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from Pydantic_Types import TransactionRequest, SubmissionResponse
from internals.Sequence_manager import Sequence_Mananger

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

sequencer = Sequence_Mananger()

async def on_app_close():
    logger.info("Now closing the app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        await sequencer.on_app_start()
        yield
        await on_app_close()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def read_root():
    return {"message": "Welcome to my FastAPI application!"}

@app.post("/api/submit", status_code=200)
async def submit_transaction(transactionReq: TransactionRequest) -> SubmissionResponse:
    (response, serverError) =   await sequencer.handel_transaction_submission(transactionRequest=transactionReq)
    if(serverError):
            raise HTTPException(status_code=500, detail="Internal server error")
    if response.valid:
        return response
    else:
        raise HTTPException(status_code=401, detail="Invalid transation")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)