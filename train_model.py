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

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

# Split data
X_train, X_test, y_train, y_test = X, X, y, y

# Train model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
r2 = model.score(X_test, y_test)
print(f"\nModel trained. R²: {r2:.3f}")
