# Smart Farm RS485 & MQTT Backend

This project implements a backend service for a Smart Farm system that synchronizes data from MQTT sensors and RS485 soil sensors. It aggregates data from multiple devices and stores it into a SQLite database with a unified timestamp.

## Features

- **MQTT Integration**: Subscribes to MQTT topics to receive temperature and humidity data from ESP32/DHT sensors.
- **RS485 Integration**: Reads soil data (Temperature, Moisture, EC) from sensors via Modbus RTU (RS485).
- **Data Synchronization**: Waits for data from all expected devices before triggering a write to the database to ensure time-aligned data.
- **SQLite Storage**: Uses a Singleton database connection to efficiently store synced data.
- **Resilience**: Includes timeout mechanisms to force data logging if not all sensors report in time.

## Prerequisites

- Python 3.x
- Hardware:
  - RS485 to USB adapter (mapped to `/dev/ttyUSB0` by default).
  - MQTT Broker.

## Installation

1.  **Clone the repository** (if applicable) or navigate to the project directory.

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Create a `.env` file in the root directory with the following variables:

```env
# MQTT Configuration
BROKER=localhost        # IP or Hostname of MQTT Broker
PORT=1883               # MQTT Port (default 1883)

# System Configuration
WAIT_TIME=30            # Timeout (seconds) to wait for all sensors before forcing save
DB_PATH=farm_data.db    # Path to SQLite database file
```

## Project Structure

```
.
├── main.py                 # Entry point of the application
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
└── src
    ├── constant
    │   ├── init.py         # Configuration constants
    │   └── query.py        # SQL queries
    ├── database
    │   └── connection.py   # Singleton SQLite database connection
    ├── mqtt.py             # MQTT Client class & logic
    └── rs485.py            # RS485 / Modbus Client class
```

## Usage

Run the main application:

```bash
python main.py
```

## How It Works

1.  The system connects to the MQTT broker and subscribes to configured topics.
2.  It listens for incoming MQTT messages from expected devices (`device1`...`device4`).
3.  When a message arrives, it's cached.
4.  Once **all** expected devices have reported, OR if the `WAIT_TIME` expires:
    - It triggers a read from the RS485 soil sensor.
    - It generates a single timestamp.
    - It saves all combined data (MQTT + RS485) into the SQLite database.
    - It clears the cache and waits for the next cycle.
