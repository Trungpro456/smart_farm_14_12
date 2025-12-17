from database.connection import DatabaseConnection
import pandas as pd
import datetime
from datetime import timedelta
from utils.time import to_vn_time
from constant.query import Query


class Database:
    def __init__(self):
        self.conn = DatabaseConnection().get_connection()
        self.cursor = self.conn.cursor()

    def get_relay_states_db(self):
        self.cursor.execute(Query.REPLAY_STATE)
        rows = self.cursor.fetchall()
        return {str(r[0]): r[1] for r in rows}

    def update_relay_state_db(self, relay_id, state):
        self.cursor.execute(Query.UPDATE_RELAY_STATE, (state, relay_id))
        self.conn.commit()

    def get_latest_ai_input(self, crop_type=1):
        try:
            self.cursor.execute(Query.GET_LATEST_AI_INPUT)
            row = self.cursor.fetchone()
            if not row:
                return None
            temp, humi = row

            self.cursor.execute(Query.GET_SOIL_DATA)
            soil_row = self.cursor.fetchone()

            if not soil_row:
                return None

            soil_moisture, soil_temp = soil_row
            crop_days = datetime.utcnow().day

            df = pd.DataFrame(
                {
                    "CropType": [crop_type],
                    "CropDays": [crop_days],
                    "SoilMoisture": [soil_moisture],
                    "Temperature": [temp],
                    "Humidity": [humi],
                }
            )

            return df
        except Exception as e:
            print("❌ Lỗi get_latest_ai_input:", e)
            return None

    def get_latest_soil_data(self):
        try:
            self.cursor.execute(Query.GET_SOIL_DATA)
            row = self.cursor.fetchone()

            if not row:
                return {"soil": None, "timestamp": None}

            vn_time = to_vn_time(row["timestamp"])
            return {
                "soil": {
                    "temperature": row["SoilTemperature"],
                    "humidity": row["SoilMoisture"],
                    "ec": row["EC"],
                    "timestamp": vn_time,
                },
                "timestamp": (datetime.utcnow() + timedelta(hours=7)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }

        except Exception as e:
            print("❌ Lỗi đọc soil_data:", e)
            return {"soil": None, "timestamp": None}

    def get_latest_sensor_data(self):
        try:
            data = {}
            for i in range(1, 5):
                table_name = f"sensor_data_{i}"
                device_key = f"device{i}"

                self.cursor.execute(f"""
                SELECT *
                FROM {table_name}
                ORDER BY server_timestamp DESC
                LIMIT 1
            """)
            row = self.cursor.fetchone()

            if row:
                vn_device_ts = to_vn_time(row["device_timestamp"])
                data[device_key] = {
                    "temp": row["Temperature"],
                    "humi": row["Humidity"],
                    "sensor": row["sensor"],
                    "device_timestamp": vn_device_ts,
                    "server_timestamp": (
                        datetime.utcnow() + timedelta(hours=7)
                    ).strftime("%Y-%m-%d %H:%M:%S"),
                }
            else:
                data[device_key] = {
                    "temp": None,
                    "humi": None,
                    "sensor": None,
                    "device_timestamp": None,
                    "server_timestamp": None,
                }

            # Timestamp chung
            data["timestamp"] = (datetime.utcnow() + timedelta(hours=7)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            return data
        except Exception as e:
            print("❌ Lỗi đọc sensor_data_all:", e)
            return {}
