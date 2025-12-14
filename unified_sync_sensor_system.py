import json
import time
import threading
import sqlite3
from datetime import datetime
import paho.mqtt.client as mqtt
from pymodbus.client.sync import ModbusSerialClient

DB_PATH = "data_sensor_all.db"

# ==========================
#  CẤU HÌNH MQTT
# ==========================

BROKER = "192.168.137.25"
PORT = 1883
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

soil_latest = None   # dữ RS485 được đọc tại đúng timestamp của MQTT


# =============================================
#  HÀM ĐỌC RS485 MỘT LẦN – đồng bộ theo timestamp
# =============================================
def read_soil_once():
    global soil_latest

    client = ModbusSerialClient(
        method="rtu",
        port="/dev/ttyUSB0",
        baudrate=9600,
        parity="N",
        stopbits=1,
        bytesize=8,
        timeout=3
    )

    if not client.connect():
        print("❌ Không mở được RS485")
        soil_latest = None
        return None

    rr = client.read_holding_registers(address=0, count=10, unit=1)
    client.close()

    if rr.isError():
        print("⚠️ Lỗi đọc RS485:", rr)
        soil_latest = None
        return None

    temp = rr.registers[1] / 10.0
    hum  = rr.registers[0] / 10.0
    ec   = rr.registers[2]
    
    soil_latest = {
        "SoilTemperature": temp,
        "SoilMoisture": hum,
        "EC": ec
    }

    print(f"🌱 RS485 Sync → Temp: {temp}°C | Moisture: {hum}% | EC: {ec}")
    return soil_latest


# =============================================
#  GHI DỮ LIỆU VÀO CSDL (5 bảng) với T chung
# =============================================
def save_synchronized_data(merged):
    T = merged["timestamp"]  # timestamp chung

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 4 bảng MQTT
        for i, dev in enumerate(EXPECTED_DEVICES.keys(), start=1):
            table = f"sensor_data_{i}"
            d = merged[dev]

            cursor.execute(f"""
                INSERT INTO {table}
                (device, Temperature, Humidity, sensor, device_timestamp, server_timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                dev,
                d["temp"],
                d["humi"],
                d["sensor"],
                T,  # đồng nhất
                T   # đồng nhất
            ))

        # Bảng soil_data
        soil = merged["soil"]

        cursor.execute("""
            INSERT INTO soil_data (timestamp, SoilTemperature, SoilMoisture, EC)
            VALUES (?, ?, ?, ?)
        """, (T, soil["SoilTemperature"], soil["SoilMoisture"], soil["EC"]))

        conn.commit()
        conn.close()

        print("💾 ĐÃ GHI 5 BẢNG VỚI T CHUNG =", T)

    except Exception as e:
        print("❌ Lỗi ghi DB:", e)


# =============================================
#  KIỂM TRA TIMEOUT MQTT
# =============================================
def check_timeout(client):
    global start_wait_time, device_data

    if start_wait_time and (time.time() - start_wait_time >= WAIT_TIME):
        print("⏰ Timeout – tạo timestamp ngay lập tức.")

        T = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        merged = {"timestamp": T}

        # Dữ liệu DHT
        for dev, sensor_type in EXPECTED_DEVICES.items():
            merged[dev] = device_data.get(dev, {
                "temp": None,
                "humi": None,
                "sensor": sensor_type
            })

        # Đọc RS485 đúng thời điểm
        read_soil_once()
        merged["soil"] = soil_latest

        save_synchronized_data(merged)

        device_data.clear()
        start_wait_time = None

    threading.Timer(1, check_timeout, args=[client]).start()


# =============================================
#  MQTT CALLBACKS
# =============================================
def on_message(client, userdata, msg):
    global device_data, start_wait_time

    try:
        data = json.loads(msg.payload.decode())
        dev = data["device"]

        device_data[dev] = {
            "temp": data.get("temp"),
            "humi": data.get("humi"),
            "sensor": data.get("sensor", EXPECTED_DEVICES[dev])
        }

        if start_wait_time is None:
            start_wait_time = time.time()

        # Nếu đã đủ 4 thiết bị → tạo timestamp
        if all(d in device_data for d in EXPECTED_DEVICES.keys()):
            T = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            merged = {"timestamp": T}

            # Thêm DHT
            for dev in EXPECTED_DEVICES.keys():
                merged[dev] = device_data[dev]

            # Đọc RS485 tại đúng thời điểm này
            read_soil_once()
            merged["soil"] = soil_latest

            save_synchronized_data(merged)

            device_data.clear()
            start_wait_time = None

    except Exception as e:
        print("❌ MQTT error:", e)


def on_connect(client, userdata, flags, rc):
    print("📡 MQTT CONNECTED")
    for topic, qos in TOPICS:
        client.subscribe(topic)
        print(f"📥 SUB: {topic}")


# =============================================
#  MAIN
# =============================================
def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, 60)
    check_timeout(client)
    client.loop_forever()


if __name__ == "__main__":
    main()
