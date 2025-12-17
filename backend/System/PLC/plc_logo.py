# plc_logo.py
# Dành cho pymodbus 2.5.3 (Raspberry Pi)

from pymodbus.client.sync import ModbusTcpClient

class LogoPLC:
    def __init__(self, host="192.168.0.3", port=502):
        self.host = host
        self.port = port

        # Kết nối test 1 lần để báo trạng thái
        test_client = ModbusTcpClient(self.host, self.port)
        ok = test_client.connect()
        print("🔌 PLC LOGO connect =", ok)
        test_client.close()

    # ---------- GHI M1..M4 ----------
    def write_relay(self, relay_id, state):
        client = ModbusTcpClient(self.host, self.port)

        if not client.connect():
            print("❌ Không kết nối được PLC khi ghi relay")
            return None

        relay_id = int(relay_id)
        base_addr = 8256                      # M1 = 8256
        coil_addr = base_addr + (relay_id - 1)
        value = True if state == "on" else False

        result = client.write_coil(coil_addr, value, unit=1)
        client.close()
        return result

    # ---------- ĐỌC Q1..Q4 ----------
    def read_outputs(self):
        # Luôn tạo client mới để tránh lỗi socket do eventlet
        client = ModbusTcpClient(self.host, self.port)

        if not client.connect():
            print("❌ Không kết nối được PLC khi đọc outputs")
            return None

        # Đọc Q1..Q4: địa chỉ 8192
        r = client.read_coils(8192, 4, unit=1)

        if not r or not hasattr(r, "bits") or len(r.bits) < 4:
            print("❌ Không đọc được Output LOGO → thử đọc M")
            r = client.read_coils(8256, 4, unit=1)

            if not r or not hasattr(r, "bits") or len(r.bits) < 4:
                print("❌ Không đọc được cả M và Q")
                client.close()
                return None

        result = {
            "1": int(r.bits[0]),
            "2": int(r.bits[1]),
            "3": int(r.bits[2]),
            "4": int(r.bits[3])
        }

        client.close()
        return result


# ---- Test nhanh ----
if __name__ == "__main__":
    plc = LogoPLC()

    print("→ Ghi M1 = ON")
    plc.write_relay(1, "on")

    print("→ Đọc Q1..Q4")
    print(plc.read_outputs())


# ---- Tạo đối tượng PLC dùng chung cho app.py ----
plc = LogoPLC()
