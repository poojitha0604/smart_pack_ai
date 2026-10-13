import re

from services.rules import transport_from_hours

STORAGE = {"Ambient", "Chilled", "Frozen"}
TRANSPORT = {"Short", "Medium", "Long"}
ALIASES = {"Chips": "Potato Chips", "Crisps": "Potato Chips", "Potato Chip": "Potato Chips"}


def normalise_food(name):
    name = re.sub(r"[_\-]+", " ", str(name)).strip().title()
    return ALIASES.get(name, name)


def parse_recommend_payload(data):
    """Return (clean_dict, error_message). Accepts travel_hours (preferred) or transportation."""
    try:
        food = normalise_food(data["food"])
        shelf_life = int(data["shelf_life"])
        storage = str(data["storage_type"]).strip().title()
        temperature = float(data["temperature"])
        hours = float(data["travel_hours"]) if data.get("travel_hours") not in (None, "") else None
        transport = transport_from_hours(hours) if hours is not None else str(data["transportation"]).strip().title()
    except (KeyError, TypeError, ValueError):
        return None, "Required: food, shelf_life (int), storage_type, travel_hours (number), temperature (number)"
    if not 1 <= shelf_life <= 365:
        return None, "shelf_life must be between 1 and 365 days"
    if hours is not None and not 0 < hours <= 720:
        return None, "travel_hours must be between 0 and 720"
    if storage not in STORAGE:
        return None, "storage_type must be one of " + ", ".join(sorted(STORAGE))
    if transport not in TRANSPORT:
        return None, "transportation must be one of " + ", ".join(sorted(TRANSPORT))
    return {"food": food, "shelf_life": shelf_life, "storage": storage, "transport": transport,
            "temperature": temperature, "travel_hours": hours}, None
