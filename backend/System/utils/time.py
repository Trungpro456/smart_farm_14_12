from datetime import datetime, timedelta

def to_vn_time(utc_str):
    try:
        utc_time = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S")
        vn_time = utc_time + timedelta(hours=7)
        return vn_time.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return utc_str
