from pydantic import BaseModel
from enum import Enum
from typing import Optional

class SubmissionResponse(BaseModel):
    message : str
    submissionId : Optional[str]
    valid : Optional[bool]

class TransactionRequest(BaseModel):
    sender : str
    receiver : str
    nonce : int
    timestamp : int
    signature: str
    amount : float

class TransactionStatus(Enum):
    SUBMITTED = "submitted"
    PENDING = "pending"
    INCLUDED = "included"
    FAILED = "failed"
    VERIFIED = "verified"


class BadgeExecutionCause(Enum):
    TIMEDOUT = "timedout"
    FILLEDUP = "filledup"
    WAITING = "waiting"


class BadgeStatus(Enum):
    ONCHAIN = "onchain"
    SUBMITTED_FOR_VERIFICATION = "submitted for verification"
    WAITING_FOR_EXECUTION = "waiting for execution"


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


# collection
class CurrentBadge(BaseModel):
    currBadgeID : str

# collection
class UsersCollection(BaseModel):
    address : str
    balance : int
    latestNonce: int
    transactions : list[str]

#collection
class TransactionBadge(BaseModel):
    badgeId : str
    status : BadgeStatus
    executionCause: Optional[BadgeExecutionCause]
    transactions : list[str]
    nextBadge : Optional["TransactionBadge"]
    prevBadge : Optional["TransactionBadge"]

    class Config:
        use_enum_values = True
