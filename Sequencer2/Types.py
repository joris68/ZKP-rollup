from pydantic import BaseModel
from enum import Enum
from typing import Optional



class TransactionStatus(Enum):
    PENDING = "pending"
    INCLUDED = "included"
    FAILED = "failed"
    VERIFIED = "verified"

#collection
class Transaction(BaseModel):
    receivedAt : int
    submissionId : str
    transactionId : str
    sender : str
    receiver : str
    nonce : int
    timestamp : int
    signature: str
    amount : float
    status : TransactionStatus
    badgeId :  str

    class Config:
        use_enum_values = True