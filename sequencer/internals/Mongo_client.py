
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()


database_connection = None

def get_mongo_client():
    global database_connection
    if database_connection is None:
        mongo_client = MongoClient(os.environ["MONGO_URI"])
        database_connection = mongo_client[os.environ["DB_NAME"]]
        return database_connection
    else :
        return database_connection