import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8783437552:AAFONe5ofVpykXqgAacmO84hGTEuTlKNsS4")
USE_REDIS = False
USE_POSTGRES = False

REDIS_URL = ""
PG_DSN = ""

PROXY_LIST = []
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]
API_KEYS = {}