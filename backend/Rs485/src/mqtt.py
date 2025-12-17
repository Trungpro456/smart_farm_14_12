import json
import time
import threading
from datetime import datetime
from src.constant.init import Constant
from src.rs485 import Rs485
from src.database.connection import DatabaseConnection


class Mqtt:
    device_data = {}
    start_wait_time = None
    rs485 = Rs485()

    @classmethod
    def check_timeout(cls, client):
        if cls.start_wait_time and (
            time.time() - cls.start_wait_time >= Constant.WAIT_TIME
        ):
            print("⏰ Timeout – tạo timestamp ngay lập tức.")

            T = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            merged = {"timestamp": T}

            # Dữ liệu DHT
            for dev, sensor_type in Constant.EXPECTED_DEVICES.items():
                merged[dev] = cls.device_data.get(
                    dev, {"temp": None, "humi": None, "sensor": sensor_type}
                )

            # Đọc RS485 đúng thời điểm
            merged["soil"] = cls.rs485.read_soil_once()

            # Save data using Singleton instance
            db = DatabaseConnection()
            db.save_synchronized_data(merged)

            cls.device_data.clear()
            cls.start_wait_time = None

        threading.Timer(1, cls.check_timeout, args=[client]).start()

    @classmethod
    def on_message(cls, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            dev = data.get("device")

            if not dev:
                print(f"⚠️ Received message without device ID: {msg.payload}")
                return

            cls.device_data[dev] = {
                "temp": data.get("temp"),
                "humi": data.get("humi"),
                "sensor": data.get("sensor", Constant.EXPECTED_DEVICES.get(dev)),
            }

            if cls.start_wait_time is None:
                cls.start_wait_time = time.time()

            # Nếu đã đủ 4 thiết bị → tạo timestamp
            if all(d in cls.device_data for d in Constant.EXPECTED_DEVICES.keys()):
                T = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                merged = {"timestamp": T}

                # Thêm DHT
                for dev in Constant.EXPECTED_DEVICES.keys():
                    merged[dev] = cls.device_data[dev]

                # Đọc RS485 tại đúng thời điểm này
                merged["soil"] = cls.rs485.read_soil_once()

                # Save data using Singleton instance
                db = DatabaseConnection()
                db.save_synchronized_data(merged)

                cls.device_data.clear()
                cls.start_wait_time = None

        except Exception as e:
            print("❌ MQTT error:", e)

    @classmethod
    def on_connect(cls, client, userdata, flags, rc):
        print("📡 MQTT CONNECTED")
        if hasattr(Constant, "TOPICS"):  # Safety check
            for topic, qos in Constant.TOPICS:
                client.subscribe(topic)
                print(f"📥 SUB: {topic}")
        else:
            print("⚠️ Constant.TOPICS not found!")
