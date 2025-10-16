import pandas as pd

# Load collected trip logs
data = pd.read_csv("data/user_trip_logs.csv")
print(data.head())
