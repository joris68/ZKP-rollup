from pymongo import MongoClient
from dotenv import load_dotenv
import os

import asyncio
import motor.motor_asyncio

load_dotenv()


async_mongo_client = None

def get_mongo_client():
    global async_mongo_client
    if async_mongo_client is None:
        client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGO_URI"])
        async_mongo_client = client
        return client
    else :
        return async_mongo_client