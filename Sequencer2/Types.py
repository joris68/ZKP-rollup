from pydantic import BaseModel
from enum import Enum
from typing import Optional



class BadgeExecutionCause(Enum):
    TIMEDOUT = "timedout"
    FILLEDUP = "filledup"


class BadgeStatus(Enum):
    SEND_TO_VERIFY = "send_to_verify"
    VERIFIED = "verified"
    FAILED = "failed"


class TransactionStatus(Enum):
    PENDING = "pending"
    INCLUDED = "included"
    FAILED = "failed"
    VERIFIED = "verified"
    INVALID = "invalid"

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
    status : Optional[TransactionStatus]
    badgeId :  str

    class Config:
        use_enum_values = True


class AccountUpdates(BaseModel):
    balance_before : int
    balance_after : int
    nonce_before : int
    nonce_after : int
    transactions : list[str]
    badgeId : str


# collection
class AccountsCollection(BaseModel):
    address : str
    balance : int
    nonce: int
    account_updates : list[AccountUpdates]


#collection
class TransactionBadge(BaseModel):
    badgeId : str
    status : BadgeStatus
    blockhash : str
    state_root : str
    blocknumber : int
    timestamp : int
    executionCause: Optional[BadgeExecutionCause]
    transactions : list[str]
    prevBadge : Optional[str]

    class Config:
        use_enum_values = True

# collection
class CurrentBadge(BaseModel):
    currBadgeID : str

