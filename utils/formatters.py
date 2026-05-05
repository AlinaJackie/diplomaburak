def format_datetime(dt, pattern="%d.%m.%Y %H:%M"):
    if not dt:
        return None
    return dt.strftime(pattern)
