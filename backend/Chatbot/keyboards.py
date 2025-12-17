from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import globals


def control_keyboard(chat_id):
    with globals.cache_lock, globals.mode_lock:
        states_copy = globals.relay_cache.copy()
        mode = globals.relay_mode.get(chat_id, "auto")

    msg = f"⚙️ **TRẠNG THÁI THIẾT BỊ** (Chế độ: {mode.upper()})\n\n"
    keyboard = []

    if mode == "manual":
        for i in range(1, 5):
            s = states_copy.get(str(i), "off")
            msg += f"• Bơm {i}: {'🟢 ON' if s == 'on' else '🔴 OFF'}\n"
            keyboard.append(
                [
                    InlineKeyboardButton(f"Bơm {i} ON", callback_data=f"on_{i}"),
                    InlineKeyboardButton(f"Bơm {i} OFF", callback_data=f"off_{i}"),
                ]
            )
    else:
        for i in range(1, 5):
            s = states_copy.get(str(i), "off")
            msg += f"• Bơm {i}: {'🟢 ON' if s == 'on' else '🔴 OFF'}\n"

    toggle_text = "Chuyển sang Manual" if mode == "auto" else "Chuyển sang Auto"
    keyboard.append([InlineKeyboardButton(toggle_text, callback_data="toggle_mode")])
    keyboard.append([InlineKeyboardButton("🏠 Menu chính", callback_data="back")])
    return msg, InlineKeyboardMarkup(keyboard)


def main_menu():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📊 Dữ liệu cảm biến", callback_data="sensor")],
            [InlineKeyboardButton("⚙️ Điều khiển thiết bị", callback_data="control")],
            [InlineKeyboardButton("❌ Thoát", callback_data="exit")],
        ]
    )
