import uuid
import time

def generate_random_id(self) -> str:
    return str(uuid.uuid4())
    
def get_current_timestamp() -> int:
    return int(time.time())