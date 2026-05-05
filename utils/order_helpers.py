import re

import requests
from flask import current_app

from constants import (
    DELIVERY_ALLOWED_CITIES,
    DELIVERY_TYPE_PICKUP,
)
from utils.city_utils import normalize_city_input, city_to_slug


def get_google_maps_api_key():
    return (current_app.config.get("GOOGLE_MAPS_API_KEY", "") or "").strip()


def get_delivery_base_fee():
    return int(current_app.config.get("DELIVERY_BASE_FEE", 40))


def get_delivery_free_from():
    return int(current_app.config.get("DELIVERY_FREE_FROM", 700))


def get_delivery_price_per_km():
    return float(current_app.config.get("DELIVERY_PRICE_PER_KM", 12))


def get_delivery_max_distance_km():
    return float(current_app.config.get("DELIVERY_MAX_DISTANCE_KM", 15))


def get_delivery_fallback_distance_km():
    return float(current_app.config.get("DELIVERY_FALLBACK_DISTANCE_KM", 4))


def get_delivery_fallback_eta_minutes():
    return int(current_app.config.get("DELIVERY_FALLBACK_ETA_MINUTES", 35))


def normalize_text(value):
    return (value or "").strip()


def normalize_city(value):
    return city_to_slug(normalize_city_input(value))


def normalize_phone(phone):
    return re.sub(r"[^\d+]", "", phone or "")


def is_valid_phone(phone):
    phone = normalize_phone(phone)
    return bool(re.fullmatch(r"^\+?380\d{9}$", phone))


def is_delivery_city_supported(city):
    return normalize_city(city) in DELIVERY_ALLOWED_CITIES


def build_full_address(city, address):
    city_part = normalize_city_input(city)
    address_part = normalize_text(address)

    if city_part and address_part:
        return f"{address_part}, {city_part}, Ukraine"
    if address_part:
        return f"{address_part}, Ukraine"
    if city_part:
        return f"{city_part}, Ukraine"
    return "Ukraine"


def _extract_eta_from_restaurant(restaurant):
    raw_eta = normalize_text(getattr(restaurant, "eta", ""))
    if not raw_eta:
        return get_delivery_fallback_eta_minutes()

    numbers = [int(value) for value in re.findall(r"\d+", raw_eta)]
    if not numbers:
        return get_delivery_fallback_eta_minutes()

    if len(numbers) == 1:
        return max(10, numbers[0])

    return max(10, round(sum(numbers[:2]) / 2))


def calculate_eta_minutes(delivery_type, restaurant, city=None, address=None):
    if delivery_type == DELIVERY_TYPE_PICKUP:
        return _extract_eta_from_restaurant(restaurant)

    route_info = calculate_route_info(restaurant, city, address)
    return route_info["eta_minutes"]


def _build_fallback_route_info(
    restaurant,
    city,
    address,
    distance_km=None,
):
    restaurant_city = normalize_city(getattr(restaurant, "city", ""))
    customer_city = normalize_city(city)

    if customer_city and restaurant_city and customer_city != restaurant_city:
        raise ValueError(
            "Доставка в інше місто для цього ресторану недоступна"
        )

    if customer_city and not is_delivery_city_supported(customer_city):
        raise ValueError("У цьому місті доставка наразі недоступна")

    eta_minutes = _extract_eta_from_restaurant(restaurant)
    fallback_distance_km = float(
        distance_km
        if distance_km is not None
        else get_delivery_fallback_distance_km()
    )

    if fallback_distance_km > get_delivery_max_distance_km():
        raise ValueError(
            "Адреса знаходиться поза зоною доставки цього ресторану"
        )

    return {
        "distance_meters": int(round(fallback_distance_km * 1000)),
        "distance_km": round(fallback_distance_km, 2),
        "eta_minutes": eta_minutes,
        "is_estimated": True,
        "source": "fallback",
    }


def geocode_address(full_address):
    google_maps_api_key = get_google_maps_api_key()
    if not google_maps_api_key:
        raise ValueError("Не задано GOOGLE_MAPS_API_KEY")

    response = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={
            "address": full_address,
            "key": google_maps_api_key,
            "language": "uk",
            "region": "ua",
        },
        timeout=15,
    )
    response.raise_for_status()

    data = response.json()

    if data.get("status") != "OK" or not data.get("results"):
        raise ValueError("Не вдалося визначити координати адреси")

    location = data["results"][0]["geometry"]["location"]

    return {
        "lat": float(location["lat"]),
        "lng": float(location["lng"]),
    }


def geocode_restaurant_location(city, address):
    full_address = build_full_address(city, address)
    return geocode_address(full_address)


def compute_route(origin_lat, origin_lng, destination_lat, destination_lng):
    google_maps_api_key = get_google_maps_api_key()
    if not google_maps_api_key:
        raise ValueError("Не задано GOOGLE_MAPS_API_KEY")

    response = requests.post(
        "https://routes.googleapis.com/directions/v2:computeRoutes",
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": google_maps_api_key,
            "X-Goog-FieldMask": "routes.duration,routes.distanceMeters",
        },
        json={
            "origin": {
                "location": {
                    "latLng": {
                        "latitude": origin_lat,
                        "longitude": origin_lng,
                    }
                }
            },
            "destination": {
                "location": {
                    "latLng": {
                        "latitude": destination_lat,
                        "longitude": destination_lng,
                    }
                }
            },
            "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_AWARE",
            "languageCode": "uk",
            "units": "METRIC",
        },
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()
    routes = data.get("routes", [])

    if not routes:
        raise ValueError("Не вдалося побудувати маршрут доставки")

    route = routes[0]
    distance_meters = int(route.get("distanceMeters", 0))
    duration_raw = route.get("duration", "0s")
    duration_seconds = int(float(duration_raw.replace("s", "")))

    return {
        "distance_meters": distance_meters,
        "distance_km": round(distance_meters / 1000, 2),
        "eta_minutes": max(1, round(duration_seconds / 60)),
        "is_estimated": False,
        "source": "google",
    }


def calculate_route_info(restaurant, city, address):
    if not restaurant:
        raise ValueError("Ресторан не знайдено")

    customer_city = normalize_city(city)
    if customer_city and not is_delivery_city_supported(customer_city):
        raise ValueError("У цьому місті доставка наразі недоступна")

    restaurant_city = normalize_city(getattr(restaurant, "city", ""))
    if customer_city and restaurant_city and customer_city != restaurant_city:
        raise ValueError(
            "Доставка в інше місто для цього ресторану недоступна"
        )

    has_coordinates = (
        getattr(restaurant, "latitude", None)
        and getattr(restaurant, "longitude", None)
    )
    if not has_coordinates:
        return _build_fallback_route_info(restaurant, city, address)

    if not get_google_maps_api_key():
        return _build_fallback_route_info(restaurant, city, address)

    try:
        destination = geocode_address(build_full_address(city, address))

        route = compute_route(
            origin_lat=float(restaurant.latitude),
            origin_lng=float(restaurant.longitude),
            destination_lat=destination["lat"],
            destination_lng=destination["lng"],
        )

        if route["distance_km"] > get_delivery_max_distance_km():
            raise ValueError(
                "Адреса знаходиться поза зоною доставки цього ресторану"
            )

        return route
    except requests.RequestException as error:
        current_app.logger.warning(
            "ROUTE API FALLBACK for restaurant_id=%s: %s",
            getattr(restaurant, "id", None),
            error,
        )
        return _build_fallback_route_info(restaurant, city, address)
    except ValueError as error:
        message = str(error)
        business_errors = (
            "поза зоною доставки",
            "доставка в інше місто",
            "доставка наразі недоступна",
        )
        if any(part in message.lower() for part in business_errors):
            raise
        current_app.logger.warning(
            "ROUTE BUSINESS FALLBACK for restaurant_id=%s: %s",
            getattr(restaurant, "id", None),
            error,
        )
        return _build_fallback_route_info(restaurant, city, address)


def calculate_delivery_fee(delivery_type, subtotal, distance_km=None):
    if delivery_type == DELIVERY_TYPE_PICKUP:
        return 0

    if subtotal >= get_delivery_free_from():
        return 0

    if distance_km is None:
        distance_km = get_delivery_fallback_distance_km()

    total = get_delivery_base_fee() + (
        float(distance_km) * get_delivery_price_per_km()
    )
    return int(round(total))