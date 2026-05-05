CATEGORY_LABELS = {
    "fastfood": "Фаст-фуд",
    "burgers": "Бургери",
    "ukrainian": "Українська",
    "breakfast": "Сніданки",
    "pizza": "Піца",
    "sushi": "Суші",
    "shawarma": "Шаурма",
    "healthy": "Корисна їжа",
    "grill": "Гриль",
    "homemade": "По-домашньому",
}

CATEGORY_ALIASES = {
    "fastfood": {
        "fastfood", "fast-food", "fast food", "фастфуд", "фаст-фуд", "фаст фуд",
    },
    "burgers": {
        "burgers", "burger", "бургери", "бургер", "бургери",
    },
    "ukrainian": {
        "ukrainian", "ukraine", "українська", "украинская", "українська кухня",
    },
    "breakfast": {
        "breakfast", "breakfasts", "сніданок", "сніданки", "завтраки",
    },
    "pizza": {
        "pizza", "піца", "пицца", "пiца",
    },
    "sushi": {
        "sushi", "суші", "суши",
    },
    "shawarma": {
        "shawarma", "шаурма", "шаверма",
    },
    "healthy": {
        "healthy", "healthy food", "корисна їжа", "здорове харчування", "здоровая еда",
    },
    "grill": {
        "grill", "гриль", "мангал",
    },
    "homemade": {
        "homemade", "home made", "по-домашньому", "домашня", "домашняя", "домашня кухня",
    },
}

_REVERSE_CATEGORY_ALIASES = {}
for slug, aliases in CATEGORY_ALIASES.items():
    _REVERSE_CATEGORY_ALIASES[slug] = slug
    for alias in aliases:
        normalized = str(alias).strip().lower()
        if normalized:
            _REVERSE_CATEGORY_ALIASES[normalized] = slug


def normalize_category_key(value):
    if value is None:
        return ""

    normalized = str(value).strip().lower()
    if not normalized:
        return ""

    return _REVERSE_CATEGORY_ALIASES.get(normalized, normalized)


def normalize_restaurant_categories(categories_value):
    if not categories_value:
        return ""

    if isinstance(categories_value, str):
        raw_items = categories_value.split(",")
    else:
        raw_items = categories_value

    normalized_items = []
    seen = set()

    for item in raw_items:
        normalized = normalize_category_key(item)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        normalized_items.append(normalized)

    return ",".join(normalized_items)


def get_category_terms(value):
    normalized = normalize_category_key(value)
    if not normalized:
        return set()

    aliases = {
        term.strip()
        for term in CATEGORY_ALIASES.get(normalized, set())
        if str(term).strip()
    }
    aliases.add(normalized)
    aliases.add(CATEGORY_LABELS.get(normalized, "").strip().lower())
    return {term for term in aliases if term}
