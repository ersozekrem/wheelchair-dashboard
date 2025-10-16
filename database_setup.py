import sqlite3

def init_db():
    conn = sqlite3.connect("wheelchair_usage.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        timestamp TEXT,
        duration_seconds REAL,
        distance_miles REAL,
        avg_speed_mph REAL,
        avg_current_a REAL,
        battery_used_ah REAL,
        battery_remaining_ah REAL,
        heater_usage_pct REAL,
        light_usage_pct REAL
    )
    """)
    conn.commit()
    conn.close()

init_db()
