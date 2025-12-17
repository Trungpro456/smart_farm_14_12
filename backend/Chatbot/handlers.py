from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import requests
import globals
from keyboards import control_keyboard, main_menu
from monitor import read_latest_from_db
from utils.validation import is_missing


async def control_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    # Initialize default Auto if not exists
    with globals.mode_lock:
        if chat_id not in globals.relay_mode:
            globals.relay_mode[chat_id] = "auto"

    if query.data == "toggle_mode":
        with globals.mode_lock:
            current = globals.relay_mode.get(chat_id, "auto")
            globals.relay_mode[chat_id] = "manual" if current == "auto" else "auto"
            # If switching to Auto, reset alert temp state so monitor_alert works
            if globals.relay_mode[chat_id] == "auto":
                globals.last_alert_temp = None
        msg, keyboard = control_keyboard(chat_id)
        await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        return

    # Only allow relay toggle when Manual
    with globals.mode_lock:
        if globals.relay_mode.get(chat_id, "auto") == "auto" and query.data.startswith(
            ("on_", "off_")
        ):
            await query.answer(
                "⚠ Chỉ có thể bật/tắt khi ở chế độ Manual", show_alert=True
            )
            return

    # Handle ON/OFF relay
    if query.data.startswith("on_") or query.data.startswith("off_"):
        action, relay = query.data.split("_")
        state = "on" if action == "on" else "off"
        try:
            url = f"{globals.SERVER_URL}/api/relay_control"
            payload = {"relay": int(relay), "state": state}
            r = requests.post(url, json=payload, timeout=5)
            r.raise_for_status()
            res = r.json()
            if res.get("success"):
                with globals.cache_lock:
                    globals.relay_cache[relay] = state
            else:
                try:
                    await query.edit_message_text(
                        f"❌ Không thể điều khiển Bơm {relay}: {res.get('message')}"
                    )
                except:
                    pass
                return
        except Exception as e:
            try:
                await query.edit_message_text(f"❌ Lỗi khi gọi server: {e}")
            except:
                pass
            return

    # Update menu
    msg, keyboard = control_keyboard(chat_id)
    try:
        await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
    except:
        pass
    globals.active_relay_menu[chat_id] = query.message.message_id


async def sensor_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    with globals.cache_lock:
        local_cache = globals.sensor_cache.copy()
    if not local_cache:
        local_cache = read_latest_from_db()

    msg = "📊 **DỮ LIỆU CẢM BIẾN (Realtime)**\n"
    has_data = False
    for dev, v in local_cache.items():
        temp = v.get("temp")
        humi = v.get("humi")
        ts = v.get("timestamp", "N/A")
        if is_missing(temp) and is_missing(humi):
            continue
        has_data = True
        temp_str = temp if not is_missing(temp) else "N/A"
        humi_str = humi if not is_missing(humi) else "N/A"
        msg += f"\n🔹 **{dev.upper()}**\n🌡 {temp_str}°C\n💧 {humi_str}%\n⏱ {ts}\n"

    if not has_data:
        msg = "⚠ Không có dữ liệu realtime!"

    keyboard = [[InlineKeyboardButton("🔙 Quay lại", callback_data="back")]]
    await query.edit_message_text(
        msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )
    globals.active_sensor_menu[query.message.chat_id] = query.message.message_id


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    intro = "🌱 **SMART FARM BOT**\nGiám sát & điều khiển AIoT\n\n**Chọn chức năng:**"
    await update.message.reply_markdown(intro, reply_markup=main_menu())


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "exit":
        await query.edit_message_text("✅ Bạn đã thoát menu.", parse_mode="Markdown")
    elif query.data == "back":
        await query.edit_message_text(
            "🌱 **SMART FARM BOT**\nChọn chức năng:",
            reply_markup=main_menu(),
            parse_mode="Markdown",
        )
    elif query.data == "sensor":
        await sensor_menu(update, context)
    elif query.data.startswith("control") or query.data.startswith(
        ("on_", "off_", "toggle_mode")
    ):
        await control_menu(update, context)
