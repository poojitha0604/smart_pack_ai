"""
Rule-based packaging logic.

Used for three things:
  1. fallback recommendation when the ML model has not been trained yet,
  2. labelling the synthetic ML dataset (ml/generate_dataset.py),
  3. building the "Why this recommendation?" explanations.
Keep this file free of imports from other backend modules.
"""

# Packaging ids are defined in database/reference_data.py (pk0 .. pk7)
ALTERNATIVE = {"pk0": "pk1", "pk1": "pk0", "pk2": "pk0", "pk3": "pk7", "pk4": "pk0", "pk5": "pk0", "pk6": "pk0", "pk7": "pk3"}
ECO_OPTION = {"pk2": "pk2", "pk6": "pk6"}  # anything else -> pk6 (biodegradable PLA)

# Explanation keys (translated in frontend/js/i18n.js) per recommended packaging
WHY = {
    "pk0": ["w_s1", "w_s2"],
    "pk1": ["w_m1", "w_m2"],
    "pk2": ["w_t1", "w_t2"],
    "pk3": ["w_c1", "w_c2", "w_c3"],
    "pk4": ["w_b1", "w_b2"],
    "pk5": ["w_f1", "w_f2"],
    "pk6": ["w_s1", "w_s2"],
    "pk7": ["w_c1", "w_c2", "w_c3"],
}


def rule_based_packaging(name, respiration, shelf_life, storage, transport):
    """Return a packaging id (pk0..pk7)."""
    if name == "Potato Chips":
        return "pk7" if shelf_life > 90 else "pk3"
    if storage == "Frozen":
        return "pk5"
    if name == "Bread":
        return "pk4"
    if name in ("Potato", "Onion"):
        return "pk2"
    if storage == "Chilled" and (transport == "Long" or shelf_life > 10) and respiration in ("High", "Medium"):
        return "pk1"
    return "pk0"


def alternative_for(pid):
    return ALTERNATIVE.get(pid, "pk0")


def eco_for(pid):
    return ECO_OPTION.get(pid, "pk6")


def explanation_keys(pid):
    return WHY.get(pid, [])


def transport_tip(transport):
    return {"Long": "tg_L", "Medium": "tg_M"}.get(transport, "tg_S")


# ---------------------------------------------------------------------------
# Packing guide: how to pack to prevent spoilage, tuned to travel time + temperature
# (all returned values are translation keys from frontend/js/i18n.js)
# ---------------------------------------------------------------------------
GROUP_BY_CATEGORY = {"c_fruit": "fruit", "c_veg": "veg", "c_root": "veg", "c_bulb": "veg",
                     "c_snack": "snack", "c_bakery": "bakery"}
PACKING_STEPS = {
    "fruit": ["pk_fruit1", "pk_fruit2", "pk_fruit3"],
    "veg": ["pk_veg1", "pk_veg2", "pk_veg3"],
    "snack": ["pk_snack1", "pk_snack2", "pk_snack3"],
    "bakery": ["pk_bake1", "pk_bake2"],
}
SPOILAGE_CAUSES = {"fruit": "sp_fruit", "veg": "sp_veg", "snack": "sp_snack", "bakery": "sp_bake"}
LONG_SHELF_LIFE_DAYS = {"fruit": 14, "veg": 21, "snack": 120, "bakery": 5}   # beyond this, risk rises


def transport_from_hours(hours):
    """Travel time in hours -> Short (<6 h) / Medium (6-24 h) / Long (>24 h)."""
    return "Short" if hours < 6 else "Medium" if hours <= 24 else "Long"


def packing_guide(food, shelf_life, storage, transport, temperature):
    """food: dict from the database (needs category, temp_min, temp_max, storage_temp)."""
    group = GROUP_BY_CATEGORY.get(food["category"], "veg")
    fresh = group in ("fruit", "veg")
    tmin, tmax = food["temp_min"], food["temp_max"]
    ideal = food["storage_temp"]

    # temperature tips
    if storage == "Frozen":
        temp_tips = [("temp_frozen", None)]
        too_warm = temperature > -15
        if too_warm:
            temp_tips.append(("temp_hot", "-18 °C"))
    elif temperature > tmax:
        temp_tips, too_warm = [("temp_hot", ideal)], True
    elif temperature < tmin:
        temp_tips, too_warm = [("temp_cold", ideal)], False
    else:
        temp_tips, too_warm = [("temp_ok", None)], False

    # simple spoilage-risk score
    score = 0
    if storage == "Frozen":
        score += 2 if too_warm else 0
    elif temperature > tmax:
        score += 1 if temperature - tmax <= 5 else 2
    elif temperature < tmin:
        score += 1
    score += {"Short": 0, "Medium": 1, "Long": 2}[transport] if fresh else (1 if transport == "Long" else 0)
    if shelf_life > LONG_SHELF_LIFE_DAYS[group]:
        score += 1
    risk = "High" if score >= 4 else "Medium" if score >= 2 else "Low"

    travel_key = "tt_%s_%s" % ("fresh" if fresh else "dry", transport[0])
    return {
        "group": group,
        "risk": risk,
        "causes": SPOILAGE_CAUSES[group],
        "packing_steps": PACKING_STEPS[group],
        "travel_tip": travel_key,
        "temperature_tips": [{"key": k, "arg": a} for k, a in temp_tips],
    }
