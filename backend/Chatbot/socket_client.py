import socketio
import asyncio
import globals
from monitor import update_relay_menu
import logging

logger = logging.getLogger(__name__)

sio = socketio.Client()
bot_application = None
bot_loop = None


def init_socket(application, loop):
    global bot_application, bot_loop
    bot_application = application
    bot_loop = loop
    try:
        sio.connect(globals.SERVER_URL)
        logger.info(f"✅ Đã kết nối SocketIO tới {globals.SERVER_URL}")
    except Exception as e:
        logger.error(f"❌ Lỗi kết nối SocketIO: {e}")


@sio.event
def connect():
    logger.info("✅ Kết nối SocketIO thành công")


@sio.event
def disconnect():
    logger.warning("❌ SocketIO bị ngắt kết nối")


@sio.on("relay_status")
def handle_relay_status(data):
    relay = str(data.get("relay"))
    state = data.get("state")
    with globals.cache_lock:
        globals.relay_cache[relay] = state
    logger.info(f"🟢 Cập nhật relay: {relay} -> {state}")

    if bot_application and bot_loop:
        for chat_id, message_id in globals.active_relay_menu.items():
            asyncio.run_coroutine_threadsafe(
                update_relay_menu(bot_application, chat_id, message_id), bot_loop
            )


@sio.on("sensor_update")
def handle_sensor_update(data):
    with globals.cache_lock:
        for dev, val in data.items():
            if dev == "timestamp":
                continue
            globals.sensor_cache[dev] = {
                "temp": val.get("temp"),
                "humi": val.get("humi"),
                "timestamp": val.get("server_timestamp"),
            }
    logger.info("📊 Cập nhật sensor cache")
