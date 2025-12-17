import sqlite3
import threading
from src.constant.init import Constant
from src.constant.query import Query


class DatabaseConnection:
    _instance = None
    _lock = threading.Lock()
    _connection = None

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance

    def get_connection(self):
        if self._connection is None:
            with self._lock:
                if self._connection is None:
                    db_path = Constant.DB_PATH
                    if not db_path:
                        pass

                    if db_path is None:
                        raise ValueError("DB_PATH environment variable is not set.")

                    self._connection = sqlite3.connect(db_path, check_same_thread=False)

        return self._connection

    def close_connection(self):
        if self._connection:
            with self._lock:
                if self._connection:
                    self._connection.close()
                    self._connection = None

    def save_synchronized_data(self, merged):
        self.get_connection()  # Ensure connection is open
        T = merged["timestamp"]  # timestamp chung

        try:
            # 4 bảng MQTT
            for i, dev in enumerate(Constant.EXPECTED_DEVICES.keys(), start=1):
                # table = f"sensor_data_{i}" # Unused variable
                d = merged[dev]

                self._connection.execute(
                    Query.INSERT_MQTT,
                    (
                        dev,
                        d["temp"],
                        d["humi"],
                        d["sensor"],
                        T,  # đồng nhất
                        T,  # đồng nhất
                    ),
                )

            # Bảng soil_data
            soil = merged["soil"]

            self._connection.execute(
                Query.INSERT_SOIL,
                (T, soil["SoilTemperature"], soil["SoilMoisture"], soil["EC"]),
            )

            self._connection.commit()
            print("💾 ĐÃ GHI 5 BẢNG VỚI T CHUNG =", T)

        except Exception as e:
            print("❌ Lỗi ghi DB:", e)
