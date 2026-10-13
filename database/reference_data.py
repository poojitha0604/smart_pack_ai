"""
Reference data used to seed the database and to build ML features.

IMPORTANT: these are typical/approximate textbook-style values.
They are NOT measured from the photograph. Verify them against published
sources (food-science and packaging literature) before using them in a report.
"""

# Level strings (High / Medium / Low / None) and category/note keys are shared with
# the frontend translation table (frontend/js/i18n.js).
FOODS = {
    "Apple":        dict(emoji="🍎", category="c_fruit",  moisture="High",   fat="Low",  ph="Acidic",  ph_min=3.3, ph_max=4.0, respiration="Medium", storage_temp="0–4 °C",   temp_min=0,  temp_max=4,  note="n_eth"),
    "Banana":       dict(emoji="🍌", category="c_fruit",  moisture="High",   fat="Low",  ph="LowAcid", ph_min=4.5, ph_max=5.2, respiration="High",   storage_temp="13–15 °C", temp_min=13, temp_max=15, note="n_chill"),
    "Mango":        dict(emoji="🥭", category="c_fruit",  moisture="High",   fat="Low",  ph="Acidic",  ph_min=3.4, ph_max=4.8, respiration="High",   storage_temp="10–13 °C", temp_min=10, temp_max=13, note="n_ripen"),
    "Orange":       dict(emoji="🍊", category="c_fruit",  moisture="High",   fat="Low",  ph="Acidic",  ph_min=3.1, ph_max=4.1, respiration="Low",    storage_temp="3–8 °C",   temp_min=3,  temp_max=8,  note="n_vent"),
    "Tomato":       dict(emoji="🍅", category="c_veg",    moisture="High",   fat="Low",  ph="Acidic",  ph_min=4.0, ph_max=4.6, respiration="High",   storage_temp="8–13 °C",  temp_min=8,  temp_max=13, note="n_ripen"),
    "Potato":       dict(emoji="🥔", category="c_root",   moisture="Medium", fat="Low",  ph="LowAcid", ph_min=5.6, ph_max=6.2, respiration="Low",    storage_temp="7–10 °C",  temp_min=7,  temp_max=10, note="n_vent"),
    "Onion":        dict(emoji="🧅", category="c_bulb",   moisture="Medium", fat="Low",  ph="LowAcid", ph_min=5.3, ph_max=5.8, respiration="Low",    storage_temp="4–10 °C",  temp_min=4,  temp_max=10, note="n_vent"),
    "Carrot":       dict(emoji="🥕", category="c_root",   moisture="High",   fat="Low",  ph="LowAcid", ph_min=5.9, ph_max=6.3, respiration="Medium", storage_temp="0–2 °C",   temp_min=0,  temp_max=2,  note="n_humid"),
    "Potato Chips": dict(emoji="🥔", category="c_snack",  moisture="Low",    fat="High", ph="Neutral", ph_min=5.5, ph_max=6.5, respiration="None",   storage_temp="15–25 °C", temp_min=15, temp_max=25, note="n_dry"),
    "Bread":        dict(emoji="🍞", category="c_bakery", moisture="Medium", fat="Low",  ph="Neutral", ph_min=5.0, ph_max=6.0, respiration="None",   storage_temp="15–25 °C", temp_min=15, temp_max=25, note="n_dry"),
}

# id -> indicative specifications (typical ranges, demo purposes)
PACKAGING = {
    "pk0": dict(name="Perforated LDPE film",           otr_level="High",    otr_value="~6000 cc/m²·day",         wvtr_level="Medium",  wvtr_value="~15 g/m²·day",   thickness="30–50 µm",          sealability="Excellent", strength="Low",    map_suitable=0, sustainability="Medium", cost_level="Low"),
    "pk1": dict(name="Breathable MAP film",            otr_level="Tuned",   otr_value="3000–10000 cc/m²·day",    wvtr_level="Medium",  wvtr_value="~10 g/m²·day",   thickness="30–60 µm",          sealability="Good",      strength="Medium", map_suitable=1, sustainability="Medium", cost_level="Medium"),
    "pk2": dict(name="Ventilated mesh / paper bag",    otr_level="VeryHigh",otr_value="open",                    wvtr_level="High",    wvtr_value="",               thickness="–",                 sealability="NoSeal",    strength="Medium", map_suitable=0, sustainability="High",   cost_level="Low"),
    "pk3": dict(name="Metallized film (BOPP/MET)",     otr_level="VeryLow", otr_value="<10 cc/m²·day",           wvtr_level="VeryLow", wvtr_value="<1 g/m²·day",    thickness="30–40 µm laminate", sealability="Excellent", strength="High",   map_suitable=1, sustainability="Low",    cost_level="Medium"),
    "pk4": dict(name="Micro-perforated PP bag",        otr_level="Medium",  otr_value="~1500 cc/m²·day",         wvtr_level="Low",     wvtr_value="~5 g/m²·day",    thickness="25–40 µm",          sealability="Good",      strength="Medium", map_suitable=0, sustainability="Medium", cost_level="Low"),
    "pk5": dict(name="Frozen-grade LDPE/PA laminate",  otr_level="Low",     otr_value="<500 cc/m²·day",          wvtr_level="Low",     wvtr_value="~5 g/m²·day",    thickness="60–90 µm",          sealability="Excellent", strength="High",   map_suitable=0, sustainability="Low",    cost_level="Medium"),
    "pk6": dict(name="Biodegradable PLA film",         otr_level="Medium",  otr_value="~1000 cc/m²·day",         wvtr_level="High",    wvtr_value="~50 g/m²·day",   thickness="25–40 µm",          sealability="Good",      strength="Medium", map_suitable=0, sustainability="High",   cost_level="High"),
    "pk7": dict(name="Aluminium laminate (N₂ flush)",  otr_level="VeryLow", otr_value="<1 cc/m²·day",            wvtr_level="VeryLow", wvtr_value="<0.5 g/m²·day",  thickness="40–60 µm",          sealability="Excellent", strength="High",   map_suitable=1, sustainability="Low",    cost_level="High"),
}
