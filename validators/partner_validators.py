from utils.city_utils import normalize_city_input


def validate_partner_application_payload(data):
    data = data or {}

    contact_person = (data.get("contact_person") or "").strip()
    brand_name = (data.get("brand_name") or "").strip()
    phone = (data.get("phone") or "").strip()
    email = (data.get("email") or "").strip()
    city = normalize_city_input(data.get("city"))
    verification_link = (data.get("verification_link") or "").strip()
    edrpou_or_ipn = (data.get("edrpou_or_ipn") or "").strip()
    business_description = (data.get("business_description") or "").strip()

    personal_data_agreement = bool(data.get("personal_data_agreement"))
    representation_agreement = bool(data.get("representation_agreement"))
    planned_locations_count_raw = data.get("planned_locations_count")

    if (
        not contact_person
        or not brand_name
        or not phone
        or not email
        or not city
        or not verification_link
        or not edrpou_or_ipn
        or not business_description
    ):
        return None, "Заповніть усі обов’язкові поля."

    if "@" not in email or "." not in email:
        return None, "Некоректний email."

    try:
        planned_locations_count = int(planned_locations_count_raw)
    except (TypeError, ValueError):
        return None, "Кількість закладів має бути числом."

    if planned_locations_count < 1:
        return None, "Кількість закладів має бути не меншою за 1."

    if not personal_data_agreement:
        return None, "Потрібно надати згоду на обробку персональних даних."

    if not representation_agreement:
        return None, (
            "Потрібно підтвердити право представляти бренд або заклад."
        )

    return {
        "contact_person": contact_person,
        "brand_name": brand_name,
        "phone": phone,
        "email": email,
        "city": city,
        "verification_link": verification_link,
        "planned_locations_count": planned_locations_count,
        "edrpou_or_ipn": edrpou_or_ipn,
        "business_description": business_description,
        "personal_data_agreement": personal_data_agreement,
        "representation_agreement": representation_agreement,
    }, None
