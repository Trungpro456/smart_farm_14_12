import threading
from constant.init import Constant

# Shared Constants
TOKEN = Constant.TELEGRAM_TOKEN
CHAT_ID = Constant.TELEGRAM_CHAT_ID
SERVER_URL = Constant.SERVER_URL
DB_PATH = Constant.DB_PATH
NGUONG_NONG = Constant.THRESHOLD_HOT
NGUONG_LANH = Constant.THRESHOLD_COLD

# Shared Global Variables
sensor_cache = {}
relay_cache = {}  # Added this as it was missing in original
relay_mode = {}  # Added this as it was missing in original
active_relay_menu = {}
active_sensor_menu = {}

last_alert_temp = None
last_alert_device = {
    "device1": False,
    "device2": False,
    "device3": False,
    "device4": False,
}

# Locks
mode_lock = threading.Lock()
cache_lock = threading.Lock()  # Added this as it was missing in original
