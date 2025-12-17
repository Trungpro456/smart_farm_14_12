
mqtt = Mqtt(app)


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
