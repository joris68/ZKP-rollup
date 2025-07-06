
from operator.src.AsyncMongoClient import get_mongo_client
import logging
import os
from operator.src.Types import AccountsCollection, TransactionBadge, BadgeStatus, CurrentBadge
import sys
import json
from operator.src.utils import generate_random_id, get_current_timestamp


logger = logging.getLogger(__name__)

class SetupService:
    def __init__(self):
        self.mongo_client = get_mongo_client()

    async def insert_start_users(self):
        db = self.mongo_client[os.environ["DB_NAME"]]
        users_collection = db[os.environ["USERS"]]
        try:
            initial_state = self.get_state_json()
            logger.info(initial_state)
            user_dicts = [
                AccountsCollection(
                    address=user["pub_key"],
                    balance=user["balance"],
                    nonce=user["nonce"],
                    account_updates=[]
                ).model_dump()
                for user in initial_state["accounts"]
            ]
            await users_collection.insert_many(user_dicts)
            logger.info("Inserted users into the database.")
        except Exception as e:
            logger.info(e)
            sys.exit(1)
    
    def get_state_json(self) -> dict:
        with open("initial_state.json", "r") as file:
            state_data = json.load(file)
        logger.info(state_data)
        return state_data
        

    async def setup_genesis_badge(self):
            state_json = self.get_state_json()
            logger.info(state_json["initial_state_root"])
            db = self.mongo_client[os.environ["DB_NAME"]]
            badges_col = db[os.environ["BADGES"]]
            geneisis_badge_id = generate_random_id()
            genesis_badge = TransactionBadge(
                badgeId=geneisis_badge_id,
                status=BadgeStatus.VERIFIED,
                blockhash= "0" * 64,
                state_root = state_json["initial_state_root"],
                blocknumber=0,
                timestamp= get_current_timestamp(),
                executionCause=None,
                transactions=[],
                prevBadge="0"
            )


            try:
                await badges_col.insert_one(genesis_badge.model_dump())
                logger.info("Genesis badge inserted successfully.")
            except Exception as e:
                logger.error(f"Error inserting genesis badge: {e}")
                sys.exit(1)
            
            badges_pointer_col= db[os.environ["CURR"]]
            badges_pointer = CurrentBadge(currBadgeID = geneisis_badge_id)
            try:
                badges_pointer_col.insert_one(badges_pointer.model_dump())
                logger.info("Inserted the genesis pointer")
            except Exception as e:
                logger.error(f"Error inserting genesis badge: {e}")
                sys.exit(1)
    
    async def on_start(self) -> None:
        await self.insert_start_users()
        await self.setup_genesis_badge()
