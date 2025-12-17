def is_missing(v):
    if v is None:
        return True
    if isinstance(v, str) and v.strip() == "":
        return True
    if str(v).strip().lower() in ["none", "null", "nan"]:
        return True
    return False
