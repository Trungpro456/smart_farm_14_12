import sqlite3
from constant.init import Constant

class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance.connection = None
        return cls._instance

    def connect(self):
        if self.connection is None:
            db_path = Constant.DB_PATH

            try:
                self.connection = sqlite3.connect(db_path, check_same_thread=False)
                print(f"Connected to database at: {db_path}")

            except sqlite3.Error as e:
                print(f"Error connecting to database: {e}")
                self.connection = None
                
        return self.connection

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
