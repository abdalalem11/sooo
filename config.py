import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "").strip()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

ACCOUNTS_DIR = "data/accounts"
TEMPLATE_DIR = "template/Tepthon"
DB_PATH = "data/factory.db"

ALLOW_USERS = os.getenv("ALLOW_USERS", "true").lower() == "true"
DEFAULT_DAYS = int(os.getenv("DEFAULT_DAYS", "30"))
MAX_DAYS = int(os.getenv("MAX_DAYS", "3650"))

os.makedirs(ACCOUNTS_DIR, exist_ok=True)
