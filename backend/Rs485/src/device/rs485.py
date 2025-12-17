from pymodbus.client.sync import ModbusSerialClient

class Rs485:
    client = None

    def __init__(self):
        self.client = ModbusSerialClient(
            method="rtu",
            port="/dev/ttyUSB0",
            baudrate=9600,
            parity="N",
            stopbits=1,
            bytesize=8,
            timeout=3,
        )
    
    def read_soil_once(self):
        if not self.client.connect():
            print("❌ Không mở được RS485")
            soil_latest = None
            return None

        rr = self.client.read_holding_registers(address=0, count=10, unit=1)
        self.client.close()

        if rr.isError():
            print("⚠️ Lỗi đọc RS485:", rr)
            soil_latest = None
            return None

        temp = rr.registers[1] / 10.0
        hum = rr.registers[0] / 10.0
        ec = rr.registers[2]

        soil_latest = {"SoilTemperature": temp, "SoilMoisture": hum, "EC": ec}

        print(f"🌱 RS485 Sync → Temp: {temp}°C | Moisture: {hum}% | EC: {ec}")
        return soil_latest
