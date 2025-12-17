
class Query:
    INSERT_MQTT = """
    INSERT INTO mqtt_data (device, temperature, humidity, sensor, device_timestamp, server_timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
    """

    INSERT_SOIL = """
    INSERT INTO soil_data (timestamp, soil_temperature, soil_moisture, ec)
    VALUES (?, ?, ?, ?)
    """