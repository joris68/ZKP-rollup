from pydantic import BaseModel,  Field
from enum import Enum
from typing import Optional


class SignatureData(BaseModel):
    pubKey: str
    signature: str

class TransactionRequest(BaseModel):
    sender : str
    receiver : str
    amount: int  
    nonce: int
    signature: SignatureData


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
    submissionId : Optional[str]
    transactionId : Optional[str]
    sender : str
    receiver : Optional[str]
    nonce : Optional[int]
    signature: Optional[str]
    amount : float
    status : Optional[TransactionStatus]
    badgeId :  Optional[str]
    pubKey : Optional[str]

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

class SubmissionResponse(BaseModel):
    submission_id : str
    valid : bool

class SubmissionStatus(BaseModel):
    submission_id : str
    status : str

class NonceResponse(BaseModel):
    nonce : int

class NonceRequest(BaseModel):
    account : str

class SubmissionStatusRequest(BaseModel):
    submission_id : str



