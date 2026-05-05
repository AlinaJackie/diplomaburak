from utils.city_utils import normalize_city_input
from validators.auth_validators import _validate_password


def validate_profile_update_payload(data):
    data = data or {}

    full_name = (data.get("full_name") or "").strip()
    city = normalize_city_input(data.get("city"))
    street = (data.get("street") or "").strip()
    house = (data.get("house") or "").strip()
    extra_info = (data.get("extra_info") or "").strip()

    if not full_name:
        return None, "Вкажіть ПІБ"

    return {
        "full_name": full_name,
        "city": city,
        "street": street,
        "house": house,
        "extra_info": extra_info,
    }, None


def validate_profile_password_payload(data):
    data = data or {}

    current_password = (data.get("current_password") or "").strip()
    new_password = (data.get("new_password") or "").strip()

    if not current_password or not new_password:
        return None, "Заповніть усі поля"

    password_error = _validate_password(new_password)
    if password_error:
        return None, password_error

    return {
        "current_password": current_password,
        "new_password": new_password,
    }, None
