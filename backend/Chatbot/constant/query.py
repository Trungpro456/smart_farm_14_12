class Query:
    SELECT_DISTINCT_DEVICE = "SELECT DISTINCT device FROM sensor_data"
    SELECT_LATEST_DATA = """
    SELECT temp, humi, device_timestamp, server_timestamp
                FROM sensor_data
                WHERE device = ?
                ORDER BY id DESC LIMIT 1
                """

    SELECT_ALL_LATEST_DATA = """
    SELECT device, temp, humi, device_timestamp, server_timestamp
    FROM sensor_data
    WHERE id IN (
        SELECT MAX(id)
        FROM sensor_data
        GROUP BY device
    )
    """
