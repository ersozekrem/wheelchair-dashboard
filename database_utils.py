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

def get_user_efficiency(user_id):
    conn = sqlite3.connect("wheelchair_usage.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT SUM(distance_miles), SUM(battery_used_ah)
        FROM trips WHERE user_id=?
    """, (user_id,))
    total_distance, total_ah = cur.fetchone()
    conn.close()
    if not total_distance or not total_ah or total_ah == 0:
        return None
    return total_distance / total_ah

def predict_range(user_id, battery_remaining_ah, avg_speed_mph, heater_usage_pct, light_usage_pct):
    base_eff = get_user_efficiency(user_id)
    if not base_eff:
        return None
    eff = base_eff
    eff *= (1 - heater_usage_pct * 0.003)
    eff *= (1 - light_usage_pct * 0.001)
    if avg_speed_mph > 15:
        eff *= (1 - (avg_speed_mph - 15) * 0.02)
    predicted_miles = battery_remaining_ah * eff
    return predicted_miles
