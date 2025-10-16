from database_utils import save_trip
import time

trip_data = {
    "user_id": "user_001",
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "duration_seconds": 120,
    "distance_miles": 0.85,
    "avg_speed_mph": 15.3,
    "avg_current_a": 9.8,
    "battery_used_ah": 1.2,
    "battery_remaining_ah": 3.8,
    "heater_usage_pct": 25,
    "light_usage_pct": 50
}

save_trip(trip_data)
print("Trip saved successfully.")
