import asyncio
import requests
from datetime import datetime
import telegram
from database.function import DatabaseFunction
from constant.query import Query
from utils.validation import is_missing
import globals
from keyboards import control_keyboard
import logging

logger = logging.getLogger(__name__)


async def safe_send(bot, chat_id, text):
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"⚠️ Lỗi gửi tin nhắn đến {chat_id}: {e}")


async def update_relay_menu(application, chat_id, message_id):
    msg, keyboard = control_keyboard(chat_id)
    bot = application.bot
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=msg,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
    except telegram.error.BadRequest:
        pass


def read_latest_from_db():
    db = DatabaseFunction()
    data = {}
    try:
        # Optimized query: Fetch all latest data in one go
        query = Query.SELECT_ALL_LATEST_DATA
        rows = db.select_data_from_db(query)

        for row in rows:
            dev = row["device"]
            ts = row["server_timestamp"] or row["device_timestamp"]
            data[dev] = {"temp": row["temp"], "humi": row["humi"], "timestamp": ts}

    except Exception as e:
        logger.error(f"❌ Lỗi đọc DB: {e}")
    return data


async def monitor_alert(context):
    bot = context.application.bot
    loop = asyncio.get_running_loop()

    try:
        db_data = read_latest_from_db()
        now = datetime.utcnow()

        # Check timeout và dữ liệu rỗng
        for device, val in db_data.items():
            temp = val.get("temp")
            humi = val.get("humi")
            ts_str = val.get("timestamp")
            try:
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except:
                ts = None

            if ts is None or (now - ts).total_seconds() > 120:
                if not globals.last_alert_device.get(device, False):
                    await safe_send(
                        bot,
                        globals.CHAT_ID,
                        f"🚨 {device.upper()} không cập nhật dữ liệu hơn 2 phút!",
                    )
                    globals.last_alert_device[device] = True
                continue

            if is_missing(temp) or is_missing(humi):
                if not globals.last_alert_device.get(device, False):
                    await safe_send(
                        bot,
                        globals.CHAT_ID,
                        f"🚨 {device.upper()} báo dữ liệu rỗng (temp/humi)!",
                    )
                    globals.last_alert_device[device] = True
                continue
            else:
                if globals.last_alert_device.get(device, False):
                    await safe_send(
                        bot,
                        globals.CHAT_ID,
                        f"✅ {device.upper()} đã hoạt động trở lại.",
                    )
                globals.last_alert_device[device] = False

        # Lấy danh sách chat đang Auto
        with globals.mode_lock:
            auto_chats = [
                cid for cid, mode in globals.relay_mode.items() if mode == "auto"
            ]

        if not auto_chats:
            return  # Không có chat nào đang Auto → bỏ qua

        # Xử lý nhiệt độ toàn hệ thống (relay 2) chỉ khi Auto
        temps = []
        for dv in db_data.values():
            try:
                temps.append(float(dv.get("temp")))
            except:
                pass

        # Kiểm tra bật/tắt relay 2
        if any(t > globals.NGUONG_NONG for t in temps):
            if globals.last_alert_temp != "relay2_on":
                for chat_id in auto_chats:
                    await safe_send(
                        bot,
                        chat_id,
                        f"🔥 Một trong các cảm biến vượt {globals.NGUONG_NONG}°C → **BẬT BƠM 2**",
                    )
                try:
                    url = f"{globals.SERVER_URL}/api/relay_control"
                    payload = {"relay": 2, "state": "on"}
                    r = requests.post(url, json=payload, timeout=5)
                    r.raise_for_status()
                    with globals.cache_lock:
                        globals.relay_cache["2"] = "on"
                    for chat_id, message_id in globals.active_relay_menu.items():
                        asyncio.run_coroutine_threadsafe(
                            update_relay_menu(context.application, chat_id, message_id),
                            loop,
                        )
                except Exception as e:
                    logger.error(f"❌ Lỗi bật relay 2: {e}")
                globals.last_alert_temp = "relay2_on"
        else:
            if globals.last_alert_temp == "relay2_on":
                for chat_id in auto_chats:
                    await safe_send(
                        bot, chat_id, f"✅ Nhiệt độ đã về mức an toàn → **TẮT BƠM 2**"
                    )
                try:
                    url = f"{globals.SERVER_URL}/api/relay_control"
                    payload = {"relay": 2, "state": "off"}
                    r = requests.post(url, json=payload, timeout=5)
                    r.raise_for_status()
                    with globals.cache_lock:
                        globals.relay_cache["2"] = "off"
                    for chat_id, message_id in globals.active_relay_menu.items():
                        asyncio.run_coroutine_threadsafe(
                            update_relay_menu(context.application, chat_id, message_id),
                            loop,
                        )
                except Exception as e:
                    logger.error(f"❌ Lỗi tắt relay 2: {e}")
                globals.last_alert_temp = None

    except Exception as e:
        logger.error(f"❌ Lỗi monitor_alert: {e}")
