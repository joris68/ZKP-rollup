from pydantic import BaseModel


class IncomingTransaction(BaseModel):
    name : str
