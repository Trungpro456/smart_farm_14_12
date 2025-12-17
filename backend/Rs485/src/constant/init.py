import os
class Constant:
    DB_PATH = os.getenv("DB_PATH")
    BROKER = os.getenv("BROKER")
    PORT = int(os.getenv("PORT"))
    WAIT_TIME = int(os.getenv("WAIT_TIME"))
    TOPICS = [
        ("device1/dht22", 0),
        ("device2/dht22", 0),
        ("device3/dht22", 0),
        ("device4/dht11", 0)
    ]

    EXPECTED_DEVICES = {
        "device1": "DHT22",
        "device2": "DHT22",
        "device3": "DHT22",
        "device4": "DHT11"
    }

    WAIT_TIME = 30
    device_data = {}
    start_wait_time = None

    soil_latest = None   