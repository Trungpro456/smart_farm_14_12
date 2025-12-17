import json
import time
import threading
from datetime import datetime
from src.constant.init import Constant
from src.rs485 import Rs485
from src.database.connection import DatabaseConnection

rs485 = Rs485()

def check_timeout(client):
    global start_wait_time, device_data

    if start_wait_time and (time.time() - start_wait_time >= Constant.WAIT_TIME):
        print("⏰ Timeout – tạo timestamp ngay lập tức.")

        T = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        merged = {"timestamp": T}

        # Dữ liệu DHT
        for dev, sensor_type in Constant.EXPECTED_DEVICES.items():
            merged[dev] = device_data.get(
                dev, {"temp": None, "humi": None, "sensor": sensor_type}
            )

        # Đọc RS485 đúng thời điểm
        merged["soil"] = rs485.read_soil_once()

        DatabaseConnection.save_synchronized_data(merged)

        device_data.clear()
        start_wait_time = None

    threading.Timer(1, check_timeout, args=[client]).start()


def on_message(client, userdata, msg):
    global device_data, start_wait_time

    try:
        data = json.loads(msg.payload.decode())
        dev = data["device"]

        device_data[dev] = {
            "temp": data.get("temp"),
            "humi": data.get("humi"),
            "sensor": data.get("sensor", Constant.EXPECTED_DEVICES[dev]),
        }

        if start_wait_time is None:
            start_wait_time = time.time()

        # Nếu đã đủ 4 thiết bị → tạo timestamp
        if all(d in device_data for d in Constant.EXPECTED_DEVICES.keys()):
            T = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            merged = {"timestamp": T}

            # Thêm DHT
            for dev in Constant.EXPECTED_DEVICES.keys():
                merged[dev] = device_data[dev]

            # Đọc RS485 tại đúng thời điểm này
            merged["soil"] = rs485.read_soil_once()

            DatabaseConnection.save_synchronized_data(merged)

            device_data.clear()
            start_wait_time = None

    except Exception as e:
        print("❌ MQTT error:", e)


def on_connect(client, userdata, flags, rc):
    print("📡 MQTT CONNECTED")
    for topic, qos in Constant.TOPICS:
        client.subscribe(topic)
        print(f"📥 SUB: {topic}")
