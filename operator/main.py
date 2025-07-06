import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fastapi import FastAPI
from pymongo import MongoClient
import logging
import json
from dotenv import load_dotenv
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from src.Types import TransactionRequest, SubmissionResponse

load_dotenv()

app = FastAPI(lifespan=lifespan)



@app.get("/")
async def read_root():
    return {"message": "Welcome to my FastAPI application!"}

@app.post("/api/submit")
async def submit_transaction(transaction: TransactionRequest) -> SubmissionResponse:
   sub_response = await sequencer.handel_transaction_submission()
   return sub_response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)