# ================== MONKEY PATCH PHẢI ĐỨNG ĐẦU ==================
import eventlet
eventlet.monkey_patch()

import json
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
from flask_mqtt import Mqtt
# ====== THƯ VIỆN AI ======
import pandas as pd
import joblib
import numpy as np
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="numpy.core.getlimits")
import tflite_runtime.interpreter as tflite
#thư viện được gọi từ class plc logo
from plc_logo import plc

# ================== CẤU HÌNH CHUNG ==================
app = Flask(__name__)
app.config["SECRET_KEY"] = "secret-key-smartfarm"

# MQTT broker
app.config["MQTT_BROKER_URL"] = "localhost"
app.config["MQTT_BROKER_PORT"] = 1883
app.config["MQTT_KEEPALIVE"] = 60

# ================== SOCKET.IO ==================
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")

# ================== MQTT ==================
mqtt = Mqtt(app)

# ================== AI MODEL (TFLITE) ==================
print("🔄 Đang tải model TFLite...")
interpreter = tflite.Interpreter(model_path="ANNmodel.tflite")
interpreter.allocate_tensors()

input_index = interpreter.get_input_details()[0]["index"]
output_index = interpreter.get_output_details()[0]["index"]

encoder = joblib.load("encoder.pkl")
scaler = joblib.load("scaler.pkl")
# ================== HỖ TRỢ THỜI GIAN ==================
def to_vn_time(utc_str):
    try:
        utc_time = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S")
        vn_time = utc_time + timedelta(hours=7)
        return vn_time.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return utc_str


# ================== TRẠNG THÁI RELAY ==================
def get_relay_states_db():
    conn = sqlite3.connect("data_sensor_all.db")
    cursor = conn.cursor()
    cursor.execute("SELECT relay_id, state FROM relay_states")
    rows = cursor.fetchall()
    conn.close()
    return {str(r[0]): r[1] for r in rows}

def update_relay_state_db(relay_id, state):
    conn = sqlite3.connect('data_sensor_all.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE relay_states SET state=? WHERE relay_id=?", (state, relay_id))
    conn.commit()
    conn.close()
#==================Đọc Trạng thái làm việc của plc===========   
def plc_status_worker():
    while True:
        try:
            states = plc.read_outputs()   # {"1":1, "2":0, ...}

            if states:
                converted = {
                    relay: ("on" if val == 1 else "off")
                    for relay, val in states.items()
                }

                socketio.emit("relay_status_all", converted)

                # cập nhật DB
                for relay, state in converted.items():
                    update_relay_state_db(relay, state)

        except Exception as e:
            print("❌ Lỗi plc_status_worker:", e)

        socketio.sleep(1)
socketio.start_background_task(plc_status_worker)
# ================== MQTT CALLBACK ==================
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    print("✅ Kết nối MQTT thành công")
    mqtt.subscribe("sensor/data")

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    topic = message.topic
    payload = message.payload.decode()
    print(f"📩 MQTT [{topic}]: {payload}")

    if topic == "sensor/data":
        try:
            data = json.loads(payload)
            save_sensor_data(data)
            socketio.emit("sensor_update", get_latest_sensor_data())
        except Exception as e:
            print("❌ Lỗi xử lý sensor/data:", e)
    

# ================== SOCKET.IO EVENTS ==================
@socketio.on("toggle_relay")
def handle_toggle_relay(data):
    relay_id = str(data.get("relay_id"))

    try:
        # Lấy trạng thái hiện tại từ DB
        current_state = get_relay_states_db().get(relay_id, "off")
        new_state = "off" if current_state == "on" else "on"

        # 1. Ghi xuống PLC LOGO
        plc.write_relay(relay_id, new_state)

        # 2. Cập nhật DB
        update_relay_state_db(relay_id, new_state)

        # 3. Phát trạng thái mới về UI
        emit("relay_status", {"relay": relay_id, "state": new_state})

        print(f"🟢 PLC LOGO: Relay {relay_id} -> {new_state}")

    except Exception as e:
        print(f"❌ Lỗi toggle_relay: {e}")
        emit("relay_error", {"message": str(e), "relay_id": relay_id})
# ================== SENSOR DATA ==================
def get_latest_sensor_data():
    """
    Lấy dữ liệu mới nhất từ 4 bảng sensor_data_1->4
    Trả về dict:
    {
        "device1": {...},
        "device2": {...},
        "device3": {...},
        "device4": {...},
        "timestamp": "..."
    }
    """
    try:
        conn = sqlite3.connect("data_sensor_all.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        data = {}
        for i in range(1, 5):
            table_name = f"sensor_data_{i}"
            device_key = f"device{i}"

            cursor.execute(f"""
                SELECT *
                FROM {table_name}
                ORDER BY server_timestamp DESC
                LIMIT 1
            """)
            row = cursor.fetchone()

            if row:
                vn_device_ts = to_vn_time(row["device_timestamp"])
                data[device_key] = {
                    "temp": row["Temperature"],
                    "humi": row["Humidity"],
                    "sensor": row["sensor"],
                    "device_timestamp": vn_device_ts,
                    "server_timestamp": (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                data[device_key] = {
                    "temp": None,
                    "humi": None,
                    "sensor": None,
                    "device_timestamp": None,
                    "server_timestamp": None
                }

        # Timestamp chung
        data["timestamp"] = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
        conn.close()
        return data
    except Exception as e:
        print("❌ Lỗi đọc sensor_data_all:", e)
        return {}

# ================== SOIL DATA ==================
def get_latest_soil_data():
    """
    Lấy dữ liệu mới nhất từ bảng soil_data
    Trả về dict giống trước:
    {
        "soil": { "temperature": ..., "humidity": ..., "ec": ..., "timestamp": ... },
        "timestamp": ...
    }
    """
    try:
        conn = sqlite3.connect("data_sensor_all.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM soil_data
            ORDER BY id DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()

        if not row:
            return {"soil": None, "timestamp": None}

        vn_time = to_vn_time(row["timestamp"])
        return {
            "soil": {
                "temperature": row["SoilTemperature"],
                "humidity": row["SoilMoisture"],
                "ec": row["EC"],
                "timestamp": vn_time
            },
            "timestamp": (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        print("❌ Lỗi đọc soil_data:", e)
        return {"soil": None, "timestamp": None}
# ================== AI INPUT (TEST MODE) ==================
"""def get_latest_ai_input(crop_type=1):
    try:
        # === GIÁ TRỊ TEST TỰ NHẬP ===
        test_data = {
            "CropType": crop_type,
            "CropDays": 30,        # bạn muốn test giá trị nào thì đổi đây
            "SoilMoisture": 60,    # đất khô -> model phải dự đoán TƯỚI
            "Temperature": 30,
            "Humidity": 80
        }

        df = pd.DataFrame([test_data])
        return df

    except Exception as e:
        print("❌ Lỗi get_latest_ai_input:", e)
        return None"""
def get_latest_ai_input(crop_type=1):
    try:
        conn = sqlite3.connect("data_sensor_all.db")
        cursor = conn.cursor()

        cursor.execute("SELECT Temperature, Humidity FROM sensor_data_1 ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        temp, humi = row

        cursor.execute("SELECT SoilMoisture, SoilTemperature FROM soil_data ORDER BY id DESC LIMIT 1")
        soil_row = cursor.fetchone()
        conn.close()

        if not soil_row:
            return None

        soil_moisture, soil_temp = soil_row
        crop_days = datetime.utcnow().day

        df = pd.DataFrame({
            "CropType": [crop_type],

            "CropDays": [crop_days],
            "SoilMoisture": [soil_moisture],
            "Temperature": [temp],
            "Humidity": [humi],
            # "NeedIrrigation": [0],  # nếu model yêu cầu
        })

        return df
    except Exception as e:
        print("❌ Lỗi get_latest_ai_input:", e)
        return None

# ================== AI PREDICT ==================
def predict_ai():
    df = get_latest_ai_input()
    if df is None:
        print("❌ Không có dữ liệu AI input")
        return {"need_irrigation": None, "confidence": None}

    print("📌 Input gốc:")
    print(df)

    # Transform
    X = encoder.transform(df)
    print("📌 Sau encoder:", X)

    X = scaler.transform(X).astype(np.float32)
    print("📌 Sau scaler:", X)

    interpreter.set_tensor(input_index, X)
    interpreter.invoke()
    y = interpreter.get_tensor(output_index)[0][0]
    print("📌 Columns after encoder:", encoder.get_feature_names_out())
    print("📌 Output mô hình (raw y):", y)
    print("📌 Kết luận mô hình:", "Tưới" if y > 0.5 else "Không tưới")
    print("📌 Độ tin cậy:", float(y))

    return {
        "need_irrigation": int(y > 0.5),
        "confidence": float(y)
    }

# ================== SOIL DATA ==================
@app.route("/soil_data")
def soil_data():
    return jsonify(get_latest_soil_data())

# ================== API ROUTES ==================
@app.route("/data")
@app.route("/data_all")
def api_data_all():
    return jsonify(get_latest_sensor_data())

@app.route("/api/relay_states")
def api_relay_states():
    relay_dict = get_relay_states_db()

    relay_list = [{"relayId": k, "state": v} for k, v in relay_dict.items()]
    return jsonify(relay_list)

@app.route("/api/relay_control", methods=["POST"])
def api_relay_control():
    data = request.get_json()
    relay_id = str(data.get("relay"))
    state = data.get("state")

    if relay_id not in ["1", "2", "3", "4"]:
        return jsonify({"error": "Relay không hợp lệ"}), 400

    try:
        plc.write_relay(relay_id, state)
        update_relay_state_db(relay_id, state)

        socketio.emit("relay_status", {"relay": relay_id, "state": state})

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/predict_ai")
def api_predict_ai():
    result = predict_ai()
    return jsonify({
        "need_irrigation": result["need_irrigation"],  # 0 hoặc 1
        "result": "Tưới" if result["need_irrigation"] == 1 else "Không tưới",
        "confidence": result["confidence"]  # VD: 0.92
    })
# ================== LOGIN ==================
@app.before_request
def require_login():
    path = (request.path or "").lower()
    public_prefixes = ("/api/", "/data", "/data_all", "/soil_data", "/socket.io", "/static", "/favicon.ico")
    for p in public_prefixes:
        if path.startswith(p):
            return
    if path in ("/login", "/api/login"):
        return
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() if request.is_json else {
        "username": request.form.get("username"),
        "password": request.form.get("password")
    }
    username = data.get("username")
    password = data.get("password")
    if username == "smartfarmAIOT" and password == "trungnlu2004":
        session["logged_in"] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Sai tài khoản hoặc mật khẩu!"})

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login_page"))

# ================== FRONTEND ROUTES ==================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/history")
def history():
    return render_template("history.html")
@app.route("/api/history")
def api_history():
    """
    Trả về lịch sử dữ liệu sensor theo device và khoảng thời gian.
    Query params:
        device: device1/device2/...
        start: YYYY-MM-DD (tùy chọn)
        end: YYYY-MM-DD (tùy chọn)
    """
    device = request.args.get("device", "device1")
    start_date = request.args.get("start")
    end_date = request.args.get("end")

    # Xác định bảng từ device
    try:
        device_map = {
            "device1": "sensor_data_1",
            "device2": "sensor_data_2",
            "device3": "sensor_data_3",
            "device4": "sensor_data_4"
        }
        table_name = device_map.get(device)
        if not table_name:
            return jsonify({"error": "Device không tồn tại"}), 400

        conn = sqlite3.connect("data_sensor_all.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = f"SELECT * FROM {table_name} WHERE 1=1"
        params = []

        if start_date:
            query += " AND date(server_timestamp) >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date(server_timestamp) <= ?"
            params.append(end_date)

        query += " ORDER BY server_timestamp ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "device": row["device"],
                "temp": row["Temperature"],
                "humi": row["Humidity"],
                "sensor": row["sensor"],
                "device_timestamp": row["device_timestamp"],
                "server_timestamp": row["server_timestamp"]
            })

        return jsonify(result)
    except Exception as e:
        print("❌ Lỗi API /api/history:", e)
        return jsonify({"error": str(e)}), 500

# ================== RUN APP ==================
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)