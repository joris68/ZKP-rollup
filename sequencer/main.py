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
from sequencer.src.Types import TransactionRequest, SubmissionResponse
from src.BadgeController import BadgeController

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

load_dotenv()

app = FastAPI()

badge_controller = BadgeController()

@app.get("/")
async def read_root():
    return {"message": "Welcome to my FastAPI application!"}

@app.post("/api/submit")
async def submit_transaction(transaction: TransactionRequest) -> SubmissionResponse:
    try:
        return await badge_controller.handel_transaction_submission(transaction_request=transaction)
    except Exception as e :
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/get-status")
async def get_status_from_transaction():
    pass
       

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)