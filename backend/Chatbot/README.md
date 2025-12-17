# 🌱 Smart Farm Telegram Chatbot

Telegram bot allows you to monitor and control Smart Farm devices (AIoT).

## ✨ Features

- **📊 Real-time Monitoring**: View temperature and humidity data from sensors in real-time.
- **⚙️ Device Control**: Control pumps (relays) manually or enable Auto mode.
- **🚨 Alerts**: Receive notifications for:
  - Sensor data timeout (> 2 minutes).
  - Sensor errors (missing data).
  - High temperature alerts (triggers automatic cooling).
- **🔄 Live Updates**: Real-time synchronization with the server using SocketIO.

## 📂 Project Structure

- `alert.py`: **Entry Point**. Initializes the bot and starts the application.
- `globals.py`: Application state and shared constants.
- `handlers.py`: Telegram command and callback handlers.
- `keyboards.py`: UI generation (buttons, menus).
- `monitor.py`: Background monitoring logic (Auto mode & Alerts).
- `socket_client.py`: SocketIO client for real-time server communication.
- `utils/`: Helper utilities (Logger, Validation).
- `database/`: Database connection and query logic.
- `constant/`: Configuration and SQL queries.

## 🚀 Installation & Setup

1.  **Clone the repository** and navigate to the `backend/telegram_chatbot` directory.

2.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuration**:

    - Ensure `constant/init.py` has the correct `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, and `SERVER_URL`.

4.  **Run the Bot**:
    ```bash
    python alert.py
    ```

## 🛠 Usage

- **/start**: Open the main menu.
- **Sensor Data**: View latest sensor readings.
- **Control Device**: Toggle manual/auto mode and control specific pumps.
