from datetime import datetime


def parse_time_to_minutes(value):
    raw = (value or "").strip()
    try:
        hour_str, minute_str = raw.split(":", 1)
        hour = int(hour_str)
        minute = int(minute_str)
    except (ValueError, AttributeError):
        return None

    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None

    return (hour * 60) + minute


def get_restaurant_open_status(restaurant, now=None):
    opening_minutes = parse_time_to_minutes(
        getattr(restaurant, "opening_time", None))
    closing_minutes = parse_time_to_minutes(
        getattr(restaurant, "closing_time", None))

    if opening_minutes is None or closing_minutes is None:
        return True

    current_dt = now or datetime.now()
    current_minutes = current_dt.hour * 60 + current_dt.minute

    if opening_minutes == closing_minutes:
        return True

    if opening_minutes < closing_minutes:
        return opening_minutes <= current_minutes <= closing_minutes

    return current_minutes >= opening_minutes or current_minutes <= closing_minutes
