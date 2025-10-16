from database_utils import get_user_efficiency

efficiency = get_user_efficiency("user_001")
if efficiency is None:
    print("No data available for this user.")
else:
    print(f"Average miles per amp-hour: {efficiency:.3f}")
