from database_utils import predict_range

predicted = predict_range(
    user_id="user_001",
    battery_remaining_ah=3.5,
    avg_speed_mph=17.0,
    heater_usage_pct=20,
    light_usage_pct=40
)

if predicted is None:
    print("Not enough data to make a prediction.")
else:
    print(f"Predicted remaining mileage: {predicted:.2f} miles")
