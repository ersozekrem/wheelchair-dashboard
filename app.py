import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import time

# Initialize app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SOLAR])
server = app.server

# --- Default config ---
default_config = {
    "max_speed": 10,
    "base_current": 0.2,
    "heater_current": 0.5,
    "light_current": 0.1,
    "current_per_speed": 0.25,
    "battery_capacity": 5.0,
    "peukert_exponent": 1.1,
    "peukert_ref_current": 1.0,
    "mileage": 15.0,
    "max_current": 3.0
}

# --- Layout ---
app.layout = dbc.Container([
    dbc.Row([
        # Sidebar controls
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

            html.Hr(),
            html.H5("Simulation Variables"),
            dbc.InputGroup([dbc.InputGroupText("Max Speed"),
                            dbc.Input(id="max_speed", type="number", value=default_config["max_speed"])]),
            dbc.InputGroup([dbc.InputGroupText("Battery Ah"),
                            dbc.Input(id="battery_capacity", type="number", value=default_config["battery_capacity"])]),
            dbc.InputGroup([dbc.InputGroupText("Mileage (mi)"),
                            dbc.Input(id="mileage", type="number", value=default_config["mileage"])]),
            dbc.InputGroup([dbc.InputGroupText("Base Current (A)"),
                            dbc.Input(id="base_current", type="number", value=default_config["base_current"], step=0.1)]),
            dbc.InputGroup([dbc.InputGroupText("Heater Current (A)"),
                            dbc.Input(id="heater_current", type="number", value=default_config["heater_current"], step=0.1)]),
            dbc.InputGroup([dbc.InputGroupText("Lights Current (A)"),
                            dbc.Input(id="light_current", type="number", value=default_config["light_current"], step=0.1)]),
            dbc.InputGroup([dbc.InputGroupText("Current per Speed (A/m/s)"),
                            dbc.Input(id="current_per_speed", type="number", value=default_config["current_per_speed"], step=0.05)]),
            dbc.InputGroup([dbc.InputGroupText("Peukert Exponent"),
                            dbc.Input(id="peukert_exponent", type="number", value=default_config["peukert_exponent"], step=0.1)]),
            dbc.InputGroup([dbc.InputGroupText("Peukert Ref Current"),
                            dbc.Input(id="peukert_ref_current", type="number", value=default_config["peukert_ref_current"], step=0.5)]),
            dbc.InputGroup([dbc.InputGroupText("Max Current (A)"),
                            dbc.Input(id="max_current", type="number", value=default_config["max_current"], step=1)]),

            dbc.Button("Apply Config", id="apply_config", color="warning", className="mt-3"),

            html.Hr(),
            html.Div(id="status", style={"color": "#06D6A0", "font-weight": "bold"})
        ], md=3, style={"backgroundColor": "#073B4C", "padding": "20px", "border-radius": "8px"}),

        # Graphs panel
        dbc.Col([
            dbc.Row([
                dbc.Col(dcc.Graph(id="speed_graph"), md=6),
                dbc.Col(dcc.Graph(id="mileage_graph"), md=6),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id="battery_graph"), md=6),
                dbc.Col(dcc.Graph(id="amperage_graph"), md=6),
            ]),
            # Current limited warning
            dbc.Row([
                dbc.Col(html.Div(id="current_limited_warning", style={"textAlign": "center", "marginTop": "10px"}))
            ])
        ], md=9)
    ]),

    # Hidden stores and timer
    dcc.Store(id="sim_state", data={"running": False, "speed": 0, "battery": default_config["battery_capacity"],
                                    "distance": 0, "start_time": time.time(), "current_limited": False}),
    dcc.Store(id="sim_config", data=default_config),
    dcc.Interval(id="sim_interval", interval=1000, n_intervals=0)
], fluid=True)


# --- Utility for Graph Styling ---
def make_bar(title, value, text, color, maxv):
    return go.Figure(go.Bar(
        x=[title], y=[value], text=[text], textposition="auto",
        marker=dict(color=color))
    ).update_yaxes(range=[0, maxv]).update_layout(template="plotly_dark",
                                                 showlegend=False,
                                                 margin=dict(l=40, r=40, t=40, b=40))

# --- Callbacks ---

# Update button text based on running state
@app.callback(
    Output("start_stop", "children"),
    Input("sim_state", "data")
)
def update_button_text(state):
    if state["running"]:
        return "■ Stop"
    else:
        return "▶ Start"

# Toggle Running
@app.callback(
    Output("sim_state", "data"),
    Input("start_stop", "n_clicks"),
    State("sim_state", "data"),
    State("sim_config", "data"),
    prevent_initial_call=True
)
def toggle_run(n, state, config):
    state["running"] = not state["running"]
    if state["running"]:
        state["start_time"] = time.time()
        state["distance"] = 0.0
        state["battery"] = config["battery_capacity"]
        state["speed"] = 0  # Reset speed when starting
    return state


# Apply Config
@app.callback(
    Output("sim_config", "data"),
    Input("apply_config", "n_clicks"),
    State("max_speed", "value"),
    State("battery_capacity", "value"),
    State("mileage", "value"),
    State("base_current", "value"),
    State("heater_current", "value"),
    State("light_current", "value"),
    State("current_per_speed", "value"),
    State("peukert_exponent", "value"),
    State("peukert_ref_current", "value"),
    State("max_current", "value"),
    prevent_initial_call=True
)
def update_config(n, max_speed, batt, mileage, base, heater, light, cps, peukert, p_ref, max_current):
    return {
        "max_speed": max_speed,
        "battery_capacity": batt,
        "mileage": mileage,
        "base_current": base,
        "heater_current": heater,
        "light_current": light,
        "current_per_speed": cps,
        "peukert_exponent": peukert,
        "peukert_ref_current": p_ref,
        "max_current": max_current,
    }


# Simulation Tick - CORRECTED
@app.callback(
    Output("sim_state", "data", allow_duplicate=True),
    Input("sim_interval", "n_intervals"),
    State("sim_state", "data"),
    State("sim_config", "data"),
    State("accessories", "value"),
    prevent_initial_call="initial_duplicate"
)
def simulation_tick(tick, state, config, accessories):
    if not state["running"]:
        return state

    # **FIX 1: Check if battery is depleted**
    if state["battery"] <= 0:
        state["battery"] = 0
        state["speed"] = 0
        state["running"] = False
        return state

    # Calculate current demand at current speed
    amps = config["base_current"] + state["speed"] * config["current_per_speed"]
    if "lights" in accessories: 
        amps += config["light_current"]
    if "heater" in accessories: 
        amps += config["heater_current"]
    
    # If current demand exceeds max, reduce speed
    if amps > config["max_current"]:
        # Calculate maximum allowed speed given current accessories
        available_current = config["max_current"] - config["base_current"]
        if "lights" in accessories: 
            available_current -= config["light_current"]
        if "heater" in accessories: 
            available_current -= config["heater_current"]
        
        # Calculate max speed that stays within current limit
        if config["current_per_speed"] > 0:
            max_allowed_speed = available_current / config["current_per_speed"]
            state["speed"] = max(0, min(state["speed"], max_allowed_speed))
            state["current_limited"] = True
        else:
            state["speed"] = 0
            state["current_limited"] = True
        
        # Recalculate current with adjusted speed
        amps = config["base_current"] + state["speed"] * config["current_per_speed"]
        if "lights" in accessories: 
            amps += config["light_current"]
        if "heater" in accessories: 
            amps += config["heater_current"]
    else:
        state["current_limited"] = False
    
    amps = max(0.01, amps)

    # Apply Peukert effect
    peukert_multiplier = (amps / config["peukert_ref_current"]) ** (config["peukert_exponent"] - 1)
    
    # Drain faster multiplier for demo speed
    DRAIN_MULTIPLIER = 10  

    # Battery drain (Ah/sec) with Peukert effect
    battery_drain = (amps/3600.0) * peukert_multiplier * DRAIN_MULTIPLIER
    state["battery"] = max(0, state["battery"] - battery_drain)
    
    # **FIX 2: Distance traveled - convert to miles to match mileage**
    # Speed is in m/s, convert to miles/s: 1 m/s = 0.000621371 miles/s
    distance_miles_per_sec = state["speed"] * 0.000621371
    state["distance"] += distance_miles_per_sec

    # Check again if battery just died
    if state["battery"] <= 0:
        state["battery"] = 0
        state["speed"] = 0
        state["running"] = False

    return state


# Handle accessory changes
@app.callback(
    Output("sim_state", "data", allow_duplicate=True),
    Input("accessories", "value"),
    State("sim_state", "data"),
    State("sim_config", "data"),
    prevent_initial_call="initial_duplicate"
)
def adjust_for_accessories(accessories, state, config):
    # Don't adjust if battery is dead
    if state["battery"] <= 0:
        state["speed"] = 0
        return state
        
    # Calculate what current would be with current speed and accessories
    amps = config["base_current"] + state["speed"] * config["current_per_speed"]
    if "lights" in accessories: 
        amps += config["light_current"]
    if "heater" in accessories: 
        amps += config["heater_current"]
    
    # If it exceeds max current, reduce speed
    if amps > config["max_current"]:
        available_current = config["max_current"] - config["base_current"]
        if "lights" in accessories: 
            available_current -= config["light_current"]
        if "heater" in accessories: 
            available_current -= config["heater_current"]
        
        if config["current_per_speed"] > 0:
            max_allowed_speed = available_current / config["current_per_speed"]
            state["speed"] = max(0, min(state["speed"], max_allowed_speed))
            state["current_limited"] = True
        else:
            state["speed"] = 0
            state["current_limited"] = True
    
    return state


# Speed Adjust - CORRECTED
@app.callback(
    Output("sim_state", "data", allow_duplicate=True),
    Input("speed_up", "n_clicks"),
    Input("speed_down", "n_clicks"),
    State("sim_state", "data"),
    State("sim_config", "data"),
    State("accessories", "value"),
    prevent_initial_call="initial_duplicate"
)
def adjust_speed(up, down, state, config, accessories):
    ctx = dash.callback_context
    if not ctx.triggered:
        return state
    
    # Don't allow speed changes if battery is dead
    if state["battery"] <= 0:
        state["speed"] = 0
        return state
        
    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger == "speed_up":
        # Calculate what the current would be at the new speed
        new_speed = state["speed"] + 1.0
        potential_amps = config["base_current"] + new_speed * config["current_per_speed"]
        
        # Add accessory current
        if "lights" in accessories: 
            potential_amps += config["light_current"]
        if "heater" in accessories: 
            potential_amps += config["heater_current"]
        
        # Only increase speed if it won't exceed max current
        if potential_amps <= config["max_current"]:
            state["speed"] = min(config["max_speed"], new_speed)
            state["current_limited"] = False
        else:
            # Calculate the maximum allowed speed
            available_current = config["max_current"] - config["base_current"]
            if "lights" in accessories: 
                available_current -= config["light_current"]
            if "heater" in accessories: 
                available_current -= config["heater_current"]
            
            if config["current_per_speed"] > 0:
                max_allowed_speed = available_current / config["current_per_speed"]
                state["speed"] = max(0, min(config["max_speed"], max_allowed_speed))
                state["current_limited"] = True
            
    elif trigger == "speed_down":
        state["speed"] = max(0, state["speed"] - 1.0)
        state["current_limited"] = False
        
    return state


# Update Graphs + Status
@app.callback(
    [Output("speed_graph", "figure"),
     Output("mileage_graph", "figure"),
     Output("battery_graph", "figure"),
     Output("amperage_graph", "figure"),
     Output("status", "children"),
     Output("current_limited_warning", "children")],
    Input("sim_state", "data"),
    State("sim_config", "data"),
    State("accessories", "value")
)
def update_graphs(state, config, accessories):
    speed, distance, battery = state["speed"], state["distance"], state["battery"]

    # Calculate current draw
    amps = config["base_current"] + speed * config["current_per_speed"]
    if "lights" in accessories: amps += config["light_current"]
    if "heater" in accessories: amps += config["heater_current"]
    
    # This should never exceed max current due to our limiting logic
    amps = min(amps, config["max_current"])

    # --- Graphs ---
    speed_fig = make_bar("Speed", speed, f"{speed:.1f} m/s", "#118AB2", config["max_speed"])
    
    # **FIX 3: Mileage left calculation - both now in miles**
    battery_percent_remaining = battery / config["battery_capacity"] if config["battery_capacity"] > 0 else 0
    mileage_left = battery_percent_remaining * config["mileage"]
    mileage_fig = make_bar("Mileage Left", mileage_left, f"{mileage_left:.1f} mi", "#FFD166", config["mileage"])
    
    battery_percent = (battery/config["battery_capacity"])*100 if config["battery_capacity"] > 0 else 0
    battery_fig = make_bar("Battery", battery_percent, f"{battery_percent:.1f} %", "#06D6A0", 100)
    amp_fig = make_bar("Amps", amps, f"{amps:.2f} A", "#EF476F", config["max_current"])

    # --- Status Info ---
    elapsed = time.time() - state["start_time"] if state["running"] else 0
    mins, secs = divmod(int(elapsed), 60)
    hours, mins = divmod(mins, 60)
    sim_time = f"{hours:02}:{mins:02}:{secs:02}"

    # Average speed calculation (distance is now in miles)
    avg_speed_mph = (distance / (elapsed / 3600)) if elapsed > 0 else 0  # miles per hour

    status = f"""
    Simulation Running: {state['running']} | 
    Simulation Time: {sim_time} | 
    Speed: {speed:.1f} m/s | 
    Avg Speed: {avg_speed_mph:.2f} mph | 
    Distance Travelled: {distance:.2f} mi | 
    Battery Remaining: {battery:.2f} Ah / {config['battery_capacity']} Ah |
    Current Draw: {amps:.2f} A / {config['max_current']} A max
    """
    
    # Warning messages
    warning = ""
    if state["battery"] <= 0:
        warning = dbc.Alert("🔋 BATTERY DEPLETED - Wheelchair stopped!", color="danger")
    elif state.get("current_limited", False):
        warning = dbc.Alert("⚠️ CURRENT LIMITED - Speed reduced to stay within max current", color="warning")

    return speed_fig, mileage_fig, battery_fig, amp_fig, status, warning


# --- Run App ---
if __name__ == "__main__":
    print("Starting wheelchair simulator at http://127.0.0.1:8050/")
    app.run(debug=True, host='127.0.0.1', port=8050)
