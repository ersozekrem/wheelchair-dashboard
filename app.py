import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import time
import joblib
import os

model_path = os.path.join("data", "battery_range_predictor.pkl")
model = joblib.load(model_path) if os.path.exists(model_path) else None

# --- App Init ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SOLAR], suppress_callback_exceptions=True)
server = app.server

# --- Default Config ---
default_config = {
    "max_speed": 10,
    "base_current": 1,
    "heater_current": 3,
    "light_current": 2,
    "current_per_speed": 1,
    "battery_capacity": 5.0,
    "peukert_exponent": 1.1,
    "peukert_ref_current": 1.0,
    "mileage": 15.0,
    "max_current": 15
}

# --- Utility Functions ---
def make_bar(title, value, text, color, maxv):
    return go.Figure(
        go.Bar(x=[title], y=[value], text=[text], textposition="auto", marker=dict(color=color))
    ).update_yaxes(range=[0, maxv]).update_layout(template="plotly_dark", showlegend=False)

def limit_speed(state, config, accessories):
    amps = config["base_current"] + state["speed"] * config["current_per_speed"]
    if "lights" in accessories: amps += config["light_current"]
    if "heater" in accessories: amps += config["heater_current"]

    if amps > config["max_current"]:
        available = config["max_current"] - config["base_current"]
        if "lights" in accessories: available -= config["light_current"]
        if "heater" in accessories: available -= config["heater_current"]
        if config["current_per_speed"] > 0:
            state["speed"] = max(0, available / config["current_per_speed"])
        state["current_limited"] = True
    else:
        state["current_limited"] = False
    return state

# --- UI Generation ---
fields = [
    ("max_speed", "Max Speed"),
    ("battery_capacity", "Battery Ah"),
    ("mileage", "Mileage (mi)"),
    ("base_current", "Base Current (A)"),
    ("heater_current", "Heater Current (A)"),
    ("light_current", "Lights Current (A)"),
    ("current_per_speed", "Current per Speed (A/m/s)"),
    ("peukert_exponent", "Peukert Exponent"),
    ("peukert_ref_current", "Peukert Ref Current"),
    ("max_current", "Max Current (A)")
]

inputs = [
    dbc.InputGroup([
        dbc.InputGroupText(label),
        dbc.Input(id=key, type="number", value=default_config[key])
    ]) for key, label in fields
]

# --- Layout ---
app.layout = dbc.Container([
    dbc.Row([
        # Sidebar
        dbc.Col([
            html.H2("♿ Wheelchair Dashboard", style={"color": "#FFD166"}),
            dbc.Button("▶ Start", id="start_stop", color="success", className="m-1"),
            dbc.Button("▲ Speed Up", id="speed_up", color="primary", className="m-1"),
            dbc.Button("▼ Speed Down", id="speed_down", color="danger", className="m-1"),
            html.Hr(),
            html.H5("Accessories"),
            dbc.Checklist(
                id="accessories",
                options=[{"label": "💡 Lights", "value": "lights"},
                         {"label": "🔥 Heater", "value": "heater"}],
                value=[], switch=True
            ),
            html.Hr(), html.H5("Simulation Variables"), *inputs,
            dbc.Button("Apply Config", id="apply_config", color="warning", className="mt-3"),
            dbc.Button("Export Logs", id="export_logs", color="info", className="mt-3"),
            html.Hr(), html.Div(id="status", style={"color": "#06D6A0", "font-weight": "bold"})
        ], md=3, style={"backgroundColor": "#073B4C", "padding": "20px", "border-radius": "8px"}),

        # Graphs
        dbc.Col([
            dbc.Row([
                dbc.Col(dcc.Graph(id="speed_graph"), md=6),
                dbc.Col(dcc.Graph(id="mileage_graph"), md=6)
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id="battery_graph"), md=6),
                dbc.Col(dcc.Graph(id="amperage_graph"), md=6)
            ]),
            dbc.Row([dbc.Col(html.Div(id="current_limited_warning", style={"textAlign": "center"}))])
        ], md=9)
    ]),
    dcc.Store(id="sim_state", data={"running": False, "speed": 0, "battery": default_config["battery_capacity"],
                                   "distance": 0, "start_time": time.time(),
                                   "current_limited": False, "cumulative_current": 0,
                                   "current_samples": 0, "trip_saved": False}),
    dcc.Store(id="sim_config", data=default_config),
    dcc.Store(id="trip_logs", data=[]),
    dcc.Interval(id="sim_interval", interval=100, n_intervals=0, disabled=True),
    dcc.Download(id="download_logs")
], fluid=True)

# --- Callbacks ---

@app.callback(Output("start_stop", "children"), Input("sim_state", "data"))
def update_button(state): 
    return "■ Stop" if state["running"] else "▶ Start"

@app.callback(Output("sim_interval", "disabled"), Input("sim_state", "data"))
def toggle_interval(state): return not state["running"]

@app.callback(
    [Output("sim_state", "data"), Output("trip_logs", "data")],
    Input("start_stop", "n_clicks"), State("sim_state", "data"),
    State("sim_config", "data"), State("trip_logs", "data"),
    prevent_initial_call=True
)
def toggle_run(_, state, config, logs):
    if state["running"] and state["distance"] > 0 and not state.get("trip_saved", False):
        elapsed = time.time() - state["start_time"]
        avg_speed = state["distance"] / (elapsed / 3600) if elapsed else 0
        avg_curr = state["cumulative_current"] / state["current_samples"] if state["current_samples"] else 0
        logs.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": int(elapsed),
            "distance_miles": round(state["distance"], 2),
            "avg_speed_mph": round(avg_speed, 2),
            "battery_remaining_ah": round(state["battery"], 2),
            "battery_used_ah": round(config["battery_capacity"] - state["battery"], 2),
            "avg_current_a": round(avg_curr, 2),
        })
        state["trip_saved"] = True
        import os
        import csv
        log_path = os.path.join("data", "user_trip_logs.csv")
        file_exists = os.path.isfile(log_path)
        fields = ["timestamp", "duration_seconds", "distance_miles",
              "avg_speed_mph", "battery_remaining_ah",
              "battery_used_ah", "avg_current_a"]
        with open(log_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            if not file_exists:
                writer.writeheader()
            writer.writerow(logs[-1])
        
        
    state["running"] = not state["running"]
    if state["running"]:
        state.update({"start_time": time.time(), "distance": 0, "battery": config["battery_capacity"],
                      "speed": 0, "cumulative_current": 0, "current_samples": 0, "trip_saved": False})
    return state, logs

@app.callback(Output("sim_config", "data"), Input("apply_config", "n_clicks"),
              [State(k, "value") for k, _ in fields], prevent_initial_call=True)
def update_config(_, *values): return {k: v for (k, _), v in zip(fields, values)}

# --- FIXED battery-depletion logging here ---
@app.callback(
    [Output("sim_state", "data", allow_duplicate=True),
     Output("trip_logs", "data", allow_duplicate=True)],
    Input("sim_interval", "n_intervals"),
    State("sim_state", "data"), State("sim_config", "data"),
    State("accessories", "value"), State("trip_logs", "data"),
    prevent_initial_call=True
)
def tick(_, state, config, accessories, logs):
    if not state["running"]: raise dash.exceptions.PreventUpdate

    # ✅ Handle battery depletion with proper logging
    if state["battery"] <= 0:
        state.update({"battery": 0, "speed": 0, "running": False})
        if not state.get("trip_saved", False) and state["distance"] > 0:
            elapsed = time.time() - state["start_time"]
            avg_speed = state["distance"] / (elapsed / 3600) if elapsed else 0
            avg_curr = state["cumulative_current"] / state["current_samples"] if state["current_samples"] else 0
            logs.append({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": int(elapsed),
                "distance_miles": round(state["distance"], 2),
                "avg_speed_mph": round(avg_speed, 2),
                "battery_remaining_ah": 0,
                "battery_used_ah": round(config["battery_capacity"], 2),
                "avg_current_a": round(avg_curr, 2)
            })
            state["trip_saved"] = True
        return state, logs

    # --- Normal simulation update ---
    state = limit_speed(state, config, accessories)
    amps = config["base_current"] + state["speed"] * config["current_per_speed"]
    if "lights" in accessories: amps += config["light_current"]
    if "heater" in accessories: amps += config["heater_current"]

    peuk = (amps / config["peukert_ref_current"]) ** (config["peukert_exponent"] - 1)
    DRAIN = 3  # Demo drain rate
    state["battery"] = max(0, state["battery"] - (amps / 3600) * peuk * DRAIN)
    state["cumulative_current"] += amps
    state["current_samples"] += 1
    state["distance"] += state["speed"] * 0.000621371
    return state, logs

@app.callback(Output("sim_state", "data", allow_duplicate=True),
              Input("accessories", "value"), State("sim_state", "data"),
              State("sim_config", "data"), prevent_initial_call=True)
def adjust_accessories(acc, state, config): return limit_speed(state, config, acc)

@app.callback(Output("sim_state", "data", allow_duplicate=True),
              Input("speed_up", "n_clicks"), Input("speed_down", "n_clicks"),
              State("sim_state", "data"), State("sim_config", "data"),
              State("accessories", "value"), prevent_initial_call=True)
def adjust_speed(up, down, state, config, acc):
    if state["battery"] <= 0: return state
    ctx = dash.ctx
    if ctx.triggered_id == "speed_up": state["speed"] = min(config["max_speed"], state["speed"] + 1)
    elif ctx.triggered_id == "speed_down": state["speed"] = max(0, state["speed"] - 1)
    return limit_speed(state, config, acc)

@app.callback(
    [Output("speed_graph", "figure"), Output("mileage_graph", "figure"),
     Output("battery_graph", "figure"), Output("amperage_graph", "figure"),
     Output("status", "children"), Output("current_limited_warning", "children")],
    Input("sim_state", "data"), State("sim_config", "data"), State("accessories", "value")
)
def update_graphs(s, c, acc):
    speed, dist, batt = s["speed"], s["distance"], s["battery"]
    # --- Predicted range (if model exists and battery info is available)
    predicted_range_text = ""
    if model:
    import numpy as np
    avg_speed = s["speed"] * 2.237  # convert m/s to mph
    avg_current = c["base_current"] + avg_speed * 0.1
    if "heater" in acc:
        avg_current += c["heater_current"]
    if "lights" in acc:
        avg_current += c["light_current"]
    battery_used = c["battery_capacity"] - s["battery"]
    battery_used = battery_used if battery_used > 0 else 0.1
    x = np.array([[avg_speed, avg_current, battery_used]])
    miles_per_ah = model.predict(x)[0]
    predicted_range_text = f" | Predicted Range: {(miles_per_ah * c['battery_capacity']):.1f} miles"
    amps = c["base_current"] + speed * c["current_per_speed"]
    if "lights" in acc: amps += c["light_current"]
    if "heater" in acc: amps += c["heater_current"]
    amps = min(amps, c["max_current"])

    b_pct = batt / c["battery_capacity"] if c["battery_capacity"] else 0
    figs = [
        make_bar("Speed", speed, f"{speed:.1f} m/s", "#118AB2", c["max_speed"]),
        make_bar("Mileage Left", b_pct * c["mileage"], f"{b_pct * c['mileage']:.1f} mi", "#FFD166", c["mileage"]),
        make_bar("Battery", b_pct * 100, f"{b_pct * 100:.1f}%", "#06D6A0", 100),
        make_bar("Amps", amps, f"{amps:.1f} A", "#EF476F", c["max_current"])
    ]

    elapsed = time.time() - s["start_time"] if s["running"] else 0
    avg_speed = dist / (elapsed / 3600) if elapsed > 0 else 0
    avg_curr = s["cumulative_current"] / s["current_samples"] if s["current_samples"] else 0
    h, rem = divmod(int(elapsed), 3600); m, sec = divmod(rem, 60)

    status = (f"Running: {s['running']} | Time {h:02}:{m:02}:{sec:02} | "
          f"Speed {speed:.1f} m/s | Dist {dist:.2f} mi | "
          f"Battery {batt:.2f}/{c['battery_capacity']} Ah | "
          f"Avg {avg_curr:.2f} A{predicted_range_text}")

    warning = (
        dbc.Alert("🔋 Battery depleted!", color="danger") if batt <= 0 else
        dbc.Alert("⚠️ Current limited!", color="warning") if s["current_limited"] else ""
    )
    return *figs, status, warning

@app.callback(Output("download_logs", "data"),
              Input("export_logs", "n_clicks"), State("trip_logs", "data"),
              prevent_initial_call=True)
def export_logs(_, logs):
    if not logs: return None
    fields = ["timestamp", "duration_seconds", "distance_miles", "avg_speed_mph",
              "battery_remaining_ah", "battery_used_ah", "avg_current_a"]
    csv = "\n".join([",".join(fields)] + [
        ",".join(str(trip.get(f, "")) for f in fields) for trip in logs
    ])
    return dict(content=csv, filename=f"wheelchair_trips_{time.strftime('%Y%m%d_%H%M%S')}.csv")

# --- Run ---
if __name__ == "__main__":
    print("✅ Wheelchair simulator running at http://127.0.0.1:8050/")
    app.run(debug=True)
