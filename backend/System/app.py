# ================== MONKEY PATCH PHẢI ĐỨNG ĐẦU ==================
import eventlet
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_socketio import SocketIO

# ====== THƯ VIỆN AI ======
import warnings

# thư viện được gọi từ class plc logo
from plc_logo import plc
from database.init import Database
from database.connection import DatabaseConnection
from AI.ai import ai

eventlet.monkey_patch()
warnings.filterwarnings("ignore", category=UserWarning, module="numpy.core.getlimits")

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret-key-smartfarm"

# MQTT broker
app.config["MQTT_BROKER_URL"] = "localhost"
app.config["MQTT_BROKER_PORT"] = 1883
app.config["MQTT_KEEPALIVE"] = 60

# Initialize Database wrapper
db = Database()

# ================== SOCKET.IO ==================
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")


@app.route("/soil_data")
def soil_data():
    return jsonify(db.get_latest_soil_data())


# ================== API ROUTES ==================
@app.route("/data")
@app.route("/data_all")
def api_data_all():
    return jsonify(db.get_latest_sensor_data())


@app.route("/api/relay_states")
def api_relay_states():
    relay_dict = db.get_relay_states_db()

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
        db.update_relay_state_db(relay_id, state)

        socketio.emit("relay_status", {"relay": relay_id, "state": state})

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/predict_ai")
def api_predict_ai():
    # Use the imported ai instance
    result = ai.predict_ai()
    return jsonify(
        {
            "need_irrigation": result["need_irrigation"],  # 0 hoặc 1
            "result": "Tưới" if result["need_irrigation"] == 1 else "Không tưới",
            "confidence": result["confidence"],  # VD: 0.92
        }
    )


# ================== LOGIN ==================
@app.before_request
def require_login():
    path = (request.path or "").lower()
    public_prefixes = (
        "/api/",
        "/data",
        "/data_all",
        "/soil_data",
        "/socket.io",
        "/static",
        "/favicon.ico",
    )
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
    data = (
        request.get_json()
        if request.is_json
        else {
            "username": request.form.get("username"),
            "password": request.form.get("password"),
        }
    )
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
            "device4": "sensor_data_4",
        }
        table_name = device_map.get(device)
        if not table_name:
            return jsonify({"error": "Device không tồn tại"}), 400

        # Use Singleton connection
        conn = DatabaseConnection().get_connection()
        # conn.row_factory = sqlite3.Row # Already set in connection.py
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
        # conn.close() # Do NOT close singleton connection

        result = []
        for row in rows:
            result.append(
                {
                    "id": row["id"],
                    "device": row["device"],
                    "temp": row["Temperature"],
                    "humi": row["Humidity"],
                    "sensor": row["sensor"],
                    "device_timestamp": row["device_timestamp"],
                    "server_timestamp": row["server_timestamp"],
                }
            )

        return jsonify(result)
    except Exception as e:
        print("❌ Lỗi API /api/history:", e)
        return jsonify({"error": str(e)}), 500


# ================== RUN APP ==================
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
