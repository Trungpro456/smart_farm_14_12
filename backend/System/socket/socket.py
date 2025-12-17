from flask_socketio import SocketIO, emit
from flask import Flask

class SocketMessage:
    socketio = None
    def __init__(self,app , async_mode, cors_allowed_origins):
        self.socketio = SocketIO(app, async_mode=async_mode, cors_allowed_origins=cors_allowed_origins)
        self.socketio.on("connect", self.on_connect)
        self.socketio.on("disconnect", self.on_disconnect)
        self.socketio.on("message", self.on_message)
        self.socketio.start_background_task(self.plc_status_worker)

    
    def on_connect(self):
        emit("message", {"data": "Connected"})
    
    def on_disconnect(self):
        emit("message", {"data": "Disconnected"})
    
    def on_message(self, data):
        emit("message", {"data": data})

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
    
    def plc_status_worker(self):
        while True:
            try:
                states = plc.read_outputs()

                if states:
                    converted = {
                    relay: ("on" if val == 1 else "off")
                    for relay, val in states.items()
                }

                self.socketio.emit("relay_status_all", converted)

                # cập nhật DB
                for relay, state in converted.items():
                    update_relay_state_db(relay, state)

            except Exception as e:
                print("❌ Lỗi plc_status_worker:", e)

            self.socketio.sleep(1)