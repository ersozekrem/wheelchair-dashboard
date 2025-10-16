import sqlite3

def save_trip(trip_data):
    conn = sqlite3.connect("wheelchair_usage.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trips (
            user_id, timestamp, duration_seconds, distance_miles,
            avg_speed_mph, avg_current_a, battery_used_ah,
            battery_remaining_ah, heater_usage_pct, light_usage_pct
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trip_data["user_id"], trip_data["timestamp"], trip_data["duration_seconds"],
        trip_data["distance_miles"], trip_data["avg_speed_mph"], trip_data["avg_current_a"],
        trip_data["battery_used_ah"], trip_data["battery_remaining_ah"],
        trip_data["heater_usage_pct"], trip_data["light_usage_pct"]
    ))
    conn.commit()
    conn.close()
