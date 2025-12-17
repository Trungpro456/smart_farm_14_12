class Query:
    REPLAY_STATE = "SELECT relay_id, state FROM relay_states"
    UPDATE_RELAY_STATE = "UPDATE relay_states SET state=? WHERE relay_id=?"
    GET_LATEST_AI_INPUT = "SELECT * FROM ai_input ORDER BY timestamp DESC LIMIT 1"
    GET_SOIL_DATA = (
        "SELECT SoilMoisture, SoilTemperature FROM soil_data ORDER BY id DESC LIMIT 1"
    )
    GET_SOIL_DATA_ALL = "SELECT * FROM soil_data"
    GET_LATEST_AI_INPUT = "SELECT * FROM ai_input ORDER BY timestamp DESC LIMIT 1"
    GET_SOIL_DATA = (
        "SELECT SoilMoisture, SoilTemperature FROM soil_data ORDER BY id DESC LIMIT 1"
    )
