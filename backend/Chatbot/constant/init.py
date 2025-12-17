from dotenv import load_dotenv
import os

load_dotenv()

class Constant:
    THRESHOLD_HOT = os.getenv("NGUONG_NONG")
    THRESHOLD_COLD = os.getenv("NGUONG_LANH")
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    SERVER_URL = os.getenv("SERVER_URL")
    DB_PATH=os.getenv("DB_PATH")