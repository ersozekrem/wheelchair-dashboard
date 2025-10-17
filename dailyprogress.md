# Daily Progress Log

## 10/14/25
- **What I worked on:**
  -  Updated button text, so it doesn't always show Start/Stop. Shows Stop when the wheelchair is on and Start when its off.
  -  Changed the base current to 1, heater current to 3, lights current to 2, current per speed to 1, and max current to 10.
  -  Changed the current draw display to show average current draw instead of instantaneous current draw
  -  Created a storage mechanism for trip logs. Stored the trip data (avg speed, distance travelled, battery remaining)
  -  Made simulation more responsive
## 10/15/25
- **What I worked on:**
  -  Ran several trips, extracted the data, and created more realistic trips with ChatGPT
  -  Improved button responsiveness and multiple unnecessary logs being created
  -  Fixed the issue where the logs dont save when the battery depletes
## 10/16/25
- **What I worked on:**
  -  Created a trip logging system that adds each trip to a CSV file
  -  Began to create a machine learning model using scikit-learn and Random Forest
  -  Integrated the trained model into the main app so it shows "Predicted Range" in the UI
