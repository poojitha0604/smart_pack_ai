"""Main logic: food + user inputs -> database lookup -> ML (or rules) -> packaging spec."""
from models import database as db
from services import ml_service, rules


def process_recommendation(food_name, shelf_life, storage_type, transportation, temperature, travel_hours=None):
    food = db.get_food(food_name)                                   # 1. reference properties
    if not food:
        raise ValueError(f"Unsupported food: {food_name}")

    method, probability, pid = "rules", None, None
    ml = ml_service.predict(food, shelf_life, storage_type, transportation, temperature)   # 2. ML
    if ml:
        pid = db.packaging_id_from_name(ml["packaging_name"])
        if pid:
            method, probability = "ml", ml["probability"]
    if not pid:                                                      # fallback if no model
        pid = rules.rule_based_packaging(food["name"], food["respiration"], shelf_life, storage_type, transportation)

    packaging = db.get_packaging(pid)                                # 3. packaging specs
    alt_id, eco_id = rules.alternative_for(pid), rules.eco_for(pid)
    db.save_prediction(food["name"], shelf_life, storage_type, transportation, temperature, packaging["name"], method)

    return {
        "food": food,
        "inputs": {"shelf_life": shelf_life, "storage_type": storage_type,
                   "transportation": transportation, "temperature": temperature, "travel_hours": travel_hours},
        "packaging": packaging,
        "alternative": db.get_packaging(alt_id),
        "eco_option": db.get_packaging(eco_id),
        "why": rules.explanation_keys(pid),
        "guide": rules.packing_guide(food, shelf_life, storage_type, transportation, temperature),
        "method": method,
        "model_probability": probability,
    }
