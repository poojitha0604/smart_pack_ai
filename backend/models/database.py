"""Tiny database layer. SQLite by default, MySQL if DB_TYPE=mysql (needs pymysql)."""
import sqlite3

from config.settings import Config
from database.reference_data import FOODS, PACKAGING

IS_MYSQL = Config.DB_TYPE == "mysql"

_SQLITE_DDL = [
    """CREATE TABLE IF NOT EXISTS foods (
        food_id INTEGER PRIMARY KEY AUTOINCREMENT, food_name TEXT UNIQUE NOT NULL, emoji TEXT,
        category TEXT, moisture_level TEXT, fat_level TEXT, ph_category TEXT, ph_min REAL, ph_max REAL,
        respiration_level TEXT, default_storage TEXT, temp_min REAL, temp_max REAL, note_key TEXT)""",
    """CREATE TABLE IF NOT EXISTS packaging_materials (
        packaging_id TEXT PRIMARY KEY, material_name TEXT NOT NULL, oxygen_barrier TEXT, otr_value TEXT,
        moisture_barrier TEXT, wvtr_value TEXT, thickness TEXT, sealability TEXT, mechanical_strength TEXT,
        map_suitability INTEGER, sustainability TEXT, cost_level TEXT)""",
    """CREATE TABLE IF NOT EXISTS predictions (
        prediction_id INTEGER PRIMARY KEY AUTOINCREMENT, food TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        shelf_life INTEGER, storage_type TEXT, transportation TEXT, temperature REAL,
        recommended_packaging TEXT, method TEXT)""",
]
_MYSQL_DDL = [
    """CREATE TABLE IF NOT EXISTS foods (
        food_id INT AUTO_INCREMENT PRIMARY KEY, food_name VARCHAR(50) UNIQUE NOT NULL, emoji VARCHAR(8),
        category VARCHAR(30), moisture_level VARCHAR(10), fat_level VARCHAR(10), ph_category VARCHAR(10),
        ph_min FLOAT, ph_max FLOAT, respiration_level VARCHAR(10), default_storage VARCHAR(60), temp_min FLOAT, temp_max FLOAT, note_key VARCHAR(30))""",
    """CREATE TABLE IF NOT EXISTS packaging_materials (
        packaging_id VARCHAR(10) PRIMARY KEY, material_name VARCHAR(80) NOT NULL, oxygen_barrier VARCHAR(15),
        otr_value VARCHAR(40), moisture_barrier VARCHAR(15), wvtr_value VARCHAR(40), thickness VARCHAR(40),
        sealability VARCHAR(15), mechanical_strength VARCHAR(15), map_suitability TINYINT(1),
        sustainability VARCHAR(15), cost_level VARCHAR(15))""",
    """CREATE TABLE IF NOT EXISTS predictions (
        prediction_id INT AUTO_INCREMENT PRIMARY KEY, food VARCHAR(50), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        shelf_life INT, storage_type VARCHAR(15), transportation VARCHAR(15), temperature FLOAT,
        recommended_packaging VARCHAR(80), method VARCHAR(10))""",
]


def _connect():
    if IS_MYSQL:
        import pymysql
        return pymysql.connect(
            host=Config.MYSQL_HOST, port=Config.MYSQL_PORT, user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD, database=Config.MYSQL_DATABASE,
            cursorclass=pymysql.cursors.DictCursor, charset="utf8mb4",
        )
    conn = sqlite3.connect(Config.SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _sql(sql):
    return sql.replace("?", "%s") if IS_MYSQL else sql


def query(sql, params=(), one=False):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(_sql(sql), params)
        rows = [dict(r) for r in cur.fetchall()]
        return (rows[0] if rows else None) if one else rows
    finally:
        conn.close()


def execute(sql, params=()):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(_sql(sql), params)
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables and (re)seed the reference tables."""
    conn = _connect()
    try:
        cur = conn.cursor()
        # Reference tables are rebuilt on every start so schema/data updates apply cleanly;
        # the predictions (history) table is kept.
        cur.execute("DROP TABLE IF EXISTS foods")
        cur.execute("DROP TABLE IF EXISTS packaging_materials")
        for ddl in (_MYSQL_DDL if IS_MYSQL else _SQLITE_DDL):
            cur.execute(ddl)
        for name, f in FOODS.items():
            cur.execute(_sql(
                "REPLACE INTO foods (food_name, emoji, category, moisture_level, fat_level, ph_category, ph_min, ph_max,"
                " respiration_level, default_storage, temp_min, temp_max, note_key) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"),
                (name, f["emoji"], f["category"], f["moisture"], f["fat"], f["ph"], f["ph_min"], f["ph_max"],
                 f["respiration"], f["storage_temp"], f["temp_min"], f["temp_max"], f["note"]))
        for pid, p in PACKAGING.items():
            cur.execute(_sql(
                "REPLACE INTO packaging_materials (packaging_id, material_name, oxygen_barrier, otr_value, moisture_barrier,"
                " wvtr_value, thickness, sealability, mechanical_strength, map_suitability, sustainability, cost_level)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"),
                (pid, p["name"], p["otr_level"], p["otr_value"], p["wvtr_level"], p["wvtr_value"], p["thickness"],
                 p["sealability"], p["strength"], p["map_suitable"], p["sustainability"], p["cost_level"]))
        conn.commit()
    finally:
        conn.close()


# ---------- helpers returning API-shaped dicts ----------
def get_food(name):
    r = query("SELECT * FROM foods WHERE LOWER(food_name) = LOWER(?)", (name,), one=True)
    if not r:
        return None
    return {
        "name": r["food_name"], "emoji": r["emoji"], "category": r["category"], "moisture": r["moisture_level"],
        "fat": r["fat_level"], "ph": r["ph_category"], "ph_min": r["ph_min"], "ph_max": r["ph_max"],
        "respiration": r["respiration_level"], "storage_temp": r["default_storage"],
        "temp_min": r["temp_min"], "temp_max": r["temp_max"], "note": r["note_key"],
    }


def get_packaging(pid):
    r = query("SELECT * FROM packaging_materials WHERE packaging_id = ?", (pid,), one=True)
    if not r:
        return None
    return {
        "id": r["packaging_id"], "name": r["material_name"], "otr_level": r["oxygen_barrier"], "otr_value": r["otr_value"],
        "wvtr_level": r["moisture_barrier"], "wvtr_value": r["wvtr_value"], "thickness": r["thickness"],
        "sealability": r["sealability"], "strength": r["mechanical_strength"], "map_suitable": bool(r["map_suitability"]),
        "sustainability": r["sustainability"], "cost_level": r["cost_level"],
    }


def packaging_id_from_name(name):
    r = query("SELECT packaging_id FROM packaging_materials WHERE material_name = ?", (name,), one=True)
    return r["packaging_id"] if r else None


def list_foods():
    return [r["food_name"] for r in query("SELECT food_name FROM foods ORDER BY food_id")]


def save_prediction(food, shelf_life, storage, transport, temp, packaging_name, method):
    execute(
        "INSERT INTO predictions (food, shelf_life, storage_type, transportation, temperature, recommended_packaging, method)"
        " VALUES (?,?,?,?,?,?,?)", (food, shelf_life, storage, transport, temp, packaging_name, method))


def history(limit=50):
    rows = query("SELECT * FROM predictions ORDER BY prediction_id DESC LIMIT " + str(int(limit)))
    for r in rows:
        r["created_at"] = str(r["created_at"])
    return rows
