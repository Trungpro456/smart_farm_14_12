import telegram
async def safe_send(bot, chat_id, msg):
    try:
        await bot.send_message(chat_id=chat_id, text=msg)
    except telegram.error.NetworkError as e:
        print(f"⚠ Lỗi mạng khi gửi message: {e}")
    except Exception as e:
        print(f"❌ Lỗi khác khi gửi message: {e}")
