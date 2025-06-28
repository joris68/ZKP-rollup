
import asyncio
from Types import Transaction, TransactionStatus
from MemPool import MemPool
from SetupService import SetupService
from BadgeController import BadgeController
import logging
from create_test_transactions import create_transaction

async def test_mempool_insertion():
    m = MemPool()
    # Define 5 example transactions
    transactions = [
        Transaction(
            receivedAt=1627841023,
            submissionId="sub_id_1",
            transactionId="trans_id_1",
            sender="addr_1",
            receiver="addr_2",
            nonce=1,
            timestamp=1627841023,
            signature="signature_1",
            amount=100.0,
            status=TransactionStatus.PENDING,
            badgeId="badge_1"
        ),
        Transaction(
            receivedAt=1627842023,
            submissionId="sub_id_2",
            transactionId="trans_id_2",
            sender="addr_1",
            receiver="addr_3",
            nonce=2,
            timestamp=1627842023,
            signature="signature_2",
            amount=200.0,
            status=TransactionStatus.PENDING,
            badgeId="badge_2"
        ),
        Transaction(
            receivedAt=1627843023,
            submissionId="sub_id_3",
            transactionId="trans_id_3",
            sender="addr_2",
            receiver="addr_4",
            nonce=3,
            timestamp=1627843023,
            signature="signature_3",
            amount=300.0,
            status=TransactionStatus.PENDING,
            badgeId="badge_3"
        ),
        Transaction(
            receivedAt=1627844023,
            submissionId="sub_id_4",
            transactionId="trans_id_4",
            sender="addr_3",
            receiver="addr_5",
            nonce=4,
            timestamp=1627844023,
            signature="signature_4",
            amount=400.0,
            status=TransactionStatus.PENDING,
            badgeId="badge_4"
        ),
        Transaction(
            receivedAt=1627845023,
            submissionId="sub_id_5",
            transactionId="trans_id_5",
            sender="addr_4",
            receiver="addr_6",
            nonce=5,
            timestamp=1627845023,
            signature="signature_5",
            amount=500.0,
            status=TransactionStatus.PENDING,
            badgeId="badge_5"
        ),
    ]

    for t in transactions:
            await m.insert_into_queue(transaction= t , submisson_id= "sub_id")


async def test_badge_extraction():
    m = MemPool()
    trans = await  m.get_transaction_for_badge()
    print(trans)

async def test_badge_extraction_time():
    m = MemPool()
    trans = await  m.get_transaction_for_badge(last_timestamp= 1)
    print(trans)


# 1. Setup service
#2. init BadgeController
#3 . make test transactions json
# test insertion and background task trigger


logging.basicConfig(
    level=logging.INFO,  # or logging.DEBUG for more detail
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


async def test_badge():
    setup = SetupService()
    await setup.on_start()
    badge_controller = BadgeController()
    transaction_task = asyncio.create_task(badge_controller.create_transaction_flow())
    task = asyncio.create_task(badge_controller.badge_execution_task())
    await asyncio.Event().wait() 

if __name__ == "__main__":
    asyncio.run(test_badge())