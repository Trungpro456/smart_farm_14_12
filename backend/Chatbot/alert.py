import asyncio
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
)
import globals
from handlers import start, menu_handler
from monitor import monitor_alert
from utils.logger import setup_logger

logger = setup_logger()


# ================= MAIN =================
def main():
    application = ApplicationBuilder().token(globals.TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(menu_handler))

    application.job_queue.run_repeating(monitor_alert, interval=10, first=1)

    # loop = asyncio.get_event_loop()
    # Providing it explicitly for compatibility if other modules need it via globals (though we didn't put it in globals).
    loop = asyncio.get_event_loop()

    # Initialize SocketIO
    try:
        from socket_client import init_socket

        init_socket(application, loop)
    except Exception as e:
        logger.warning(f"⚠️ Không thể khởi động SocketIO: {e}")

    logger.info("🤖 Telegram bot đang chạy...")
    application.run_polling()


if __name__ == "__main__":
    main()
