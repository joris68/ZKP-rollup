
import asyncio
from Types import Transaction, TransactionStatus
from MemPool import MemPool


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
    trans = await  m.get_badge_for_badge_size()
    print(trans)

async def test_badge_extraction_time():
    m = MemPool()
    trans = await  m.get_badge_for_badge_size(last_timestamp= 1)
    print(trans)



if __name__ =="__main__":
    asyncio.run(test_badge_extraction_time())