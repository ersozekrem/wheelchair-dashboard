import pandas as pd

# Load collected trip logs
data = pd.read_csv("data/user_trip_logs.csv")
print(data.head())

# Compute target: miles per amp-hour
data["miles_per_ah"] = data["distance_miles"] / data["battery_used_ah"]

# Define features (inputs) and target
X = data[["avg_speed_mph", "avg_current_a", "battery_used_ah"]]
y = data["miles_per_ah"]

print("\nPrepared dataset:")
print(data[["avg_speed_mph", "avg_current_a", "battery_used_ah", "miles_per_ah"]].head())
