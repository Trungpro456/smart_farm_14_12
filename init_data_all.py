import sqlite3

# ===============================
#  KẾT NỐI / TẠO FILE CSDL
# ===============================
conn = sqlite3.connect("data_sensor_all.db")
cursor = conn.cursor()

print("🔧 Đang tạo các bảng...")

# ===============================
#  BẢNG 1–4: sensor_data_1 → sensor_data_4
# ===============================

for i in range(1, 5):
    table_name = f"sensor_data_{i}"

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device TEXT,
        Temperature REAL,
        Humidity REAL,
        sensor TEXT,
        device_timestamp TEXT,
        server_timestamp TEXT
    )
    """)

    print(f"✅ Đã tạo bảng: {table_name}")

# ===============================
#  BẢNG 5: soil_data
# ===============================

cursor.execute("""
CREATE TABLE IF NOT EXISTS soil_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    SoilTemperature REAL,
    SoilMoisture REAL,
    EC REAL
)
""")
print("✅ Đã tạo bảng: soil_data")


# ===============================
#  BẢNG 6 (THAY THẾ): relay_states
# ===============================

cursor.execute("""
CREATE TABLE IF NOT EXISTS relay_states (
    relay_id INTEGER PRIMARY KEY,
    state TEXT NOT NULL
)
""")
print("✅ Đã tạo bảng: relay_states")

# Khởi tạo 4 relay mặc định = off
for i in range(1, 5):
    cursor.execute(
        "INSERT OR IGNORE INTO relay_states (relay_id, state) VALUES (?, ?)",
        (i, "off")
    )

print("🔧 Đã khởi tạo 4 relay mặc định = off")

# ===============================
#  LƯU VÀ ĐÓNG
# ===============================
conn.commit()
conn.close()

print("\n🎉 HOÀN TẤT: Đã tạo 6 bảng (bao gồm relay_states)")
