from database.connection import DatabaseConnection
class DatabaseFunction:
    connection = None
    def __init__(self):
        self.connection = DatabaseConnection().connect()

    def select_data_from_db(self,query, data=None):
        cursor = self.connection.cursor()
        cursor.execute(query, data)
        rows = cursor.fetchall()
        return rows

    def insert_data_to_db(self,query, data=None):
        cursor = self.connection.cursor()
        cursor.execute(query, data)
        self.connection.commit()
        return cursor.lastrowid
    
    def update_data_to_db(self,query, data=None):
        cursor = self.connection.cursor()
        cursor.execute(query, data)
        self.connection.commit()
        return cursor.lastrowid
    
    def delete_data_to_db(self,query, data=None):
        cursor = self.connection.cursor()
        cursor.execute(query, data)
        self.connection.commit()
        return cursor.lastrowid