import random
from config import PROXY_LIST

def get_random_proxy() -> str | None:
    if not PROXY_LIST:
        return None
    return random.choice(PROXY_LIST)