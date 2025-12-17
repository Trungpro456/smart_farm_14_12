import sys
import os

# Adjust path to import DatabaseConnection
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from connection import DatabaseConnection


def test_singleton():
    print("Testing Singleton Database Connection...")

    # Get first instance
    db1 = DatabaseConnection()
    conn1 = db1.connect()

    # Get second instance
    db2 = DatabaseConnection()
    conn2 = db2.connect()

    # Check if instances are the same
    if db1 is db2:
        print("PASS: DatabaseConnection instances are the same.")
    else:
        print("FAIL: DatabaseConnection instances are DIFFERENT.")

    # Check if connections are the same object (since they are stored in the singleton instance)
    if conn1 is conn2:
        print("PASS: SQLite connection objects are the same.")
    else:
        print("FAIL: SQLite connection objects are DIFFERENT.")

    # Test query
    try:
        cursor = conn1.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"PASS: Query executed successfully. Result: {result}")
    except Exception as e:
        print(f"FAIL: Query failed. Error: {e}")

    # Clean up
    db1.close()
    print("Connection closed.")


if __name__ == "__main__":
    test_singleton()
