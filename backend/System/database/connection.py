import sqlite3
import os
import threading


class DatabaseConnection:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, "data_sensor_all.db")
        self.connection = None
        self._initialized = True

    def get_connection(self):

        if self.connection is None:
            try:
                self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
                self.connection.row_factory = sqlite3.Row
                print(f"Successfully connected to database at: {self.db_path}")
            except sqlite3.Error as e:
                print(f"Error connecting to database: {e}")
                raise e
        return self.connection

    def close_connection(self):
        
        if self.connection:
            try:
                self.connection.close()
                print("Database connection closed.")
            except sqlite3.Error as e:
                print(f"Error closing database: {e}")
            finally:
                self.connection = None
    
    def get_cursor(self):
        return self.connection.cursor()
    
    def read_data(self, query):
        cursor = self.connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows
    
    def write_data(self, query):
        cursor = self.connection.cursor()
        cursor.execute(query)
        self.connection.commit()


# Create a global instance for easy access
db_instance = DatabaseConnection()
