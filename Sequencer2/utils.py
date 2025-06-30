import uuid
import time

def generate_random_id() -> str:
    return str(uuid.uuid4())
    
def get_current_timestamp() -> int:
    return int(time.time())