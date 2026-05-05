CITY_SLUG_TO_NAME = {
    "ivano-frankivsk": "Івано-Франківськ",
    "lviv": "Львів",
    "chernivtsi": "Чернівці",
    "kyiv": "Київ",
}

CITY_NAME_TO_SLUG = {name: slug for slug, name in CITY_SLUG_TO_NAME.items()}


def normalize_city_input(city_value):
    if not city_value:
        return ""

    value = str(city_value).strip()
    if not value:
        return ""

    lowered = value.lower()

    if lowered in CITY_SLUG_TO_NAME:
        return CITY_SLUG_TO_NAME[lowered]

    aliases = {
        "ивано-франковск": "Івано-Франківськ",
        "ивано-франківськ": "Івано-Франківськ",
        "ivanofrankivsk": "Івано-Франківськ",
        "ivano frankivsk": "Івано-Франківськ",
        "львов": "Львів",
        "lvov": "Львів",
        "киев": "Київ",
        "kiev": "Київ",
        "kyiv": "Київ",
        "черновцы": "Чернівці",
        "chernovtsy": "Чернівці",
    }

    if lowered in aliases:
        return aliases[lowered]

    for city_name in CITY_NAME_TO_SLUG:
        if city_name.lower() == lowered:
            return city_name

    return value


def city_to_slug(city_value):
    if not city_value:
        return ""

    value = str(city_value).strip()
    if not value:
        return ""

    lowered = value.lower()

    if lowered in CITY_SLUG_TO_NAME:
        return lowered

    normalized_name = normalize_city_input(value)
    return CITY_NAME_TO_SLUG.get(normalized_name, lowered)
