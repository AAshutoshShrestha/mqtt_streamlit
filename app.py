import streamlit as st
import time
from mqtt_client import MQTTClient
from dotenv import load_dotenv

# Must be first Streamlit command
st.set_page_config(layout="wide")

# Initialize session state
if 'mqtt_client' not in st.session_state:
    st.session_state.mqtt_client = MQTTClient()
    st.session_state.mqtt_client.connect()

# Initialize device state
if 'relays' not in st.session_state:
    st.session_state.relays = {f"R{i}": False for i in range(1, 33)}

if 'digital_inputs' not in st.session_state:
    st.session_state.digital_inputs = {f"D{i}": False for i in range(1, 17)}

if 'analog_inputs' not in st.session_state:
    st.session_state.analog_inputs = {f"A{i}": 0 for i in range(1, 17)}

if 'temperature_sensors' not in st.session_state:
    st.session_state.temperature_sensors = {f"T{i}": 0.0 for i in range(1, 6)}

def process_messages():
    messages = st.session_state.mqtt_client.get_messages()
    for msg_type, content in messages:
        if msg_type == "connect":
            st.toast(content, icon="✅")
            st.session_state.mqtt_client.request_state()
        elif msg_type == "error":
            st.error(content)
        elif msg_type == "message":
            # Update relays (R1-R32)
            for i in range(1, 33):
                relay_key = f"R{i}"
                if relay_key in content:
                    st.session_state.relays[relay_key] = bool(content[relay_key].get("on", 0))
            
            # Update digital inputs (D1-D16)
            for i in range(1, 17):
                digital_key = f"D{i}"
                if digital_key in content:
                    st.session_state.digital_inputs[digital_key] = bool(content[digital_key].get("on", 0))
            
            # Update analog inputs (A1-A16)
            for i in range(1, 17):
                analog_key = f"A{i}"
                if analog_key in content:
                    st.session_state.analog_inputs[analog_key] = float(content[analog_key].get("value", 0))
            
            # Update temperature sensors (T1-T5)
            for i in range(1, 6):
                temp_key = f"T{i}"
                if temp_key in content:
                    st.session_state.temperature_sensors[temp_key] = float(content[temp_key].get("value", 0.0))

# UI Layout
st.title("🟢 Kincony COLB Smart Home Controller")

# Process messages
process_messages()

# Connection status
if st.session_state.mqtt_client.connected:
    st.success("MQTT Connected", icon="✅")
else:
    st.warning("Connecting to MQTT...", icon="⚠️")

# Relay Control
st.subheader("Relay Control Panel")
cols = st.columns(4)

for i in range(1, 33):
    with cols[(i-1) % 4]:
        relay_key = f"R{i}"
        label = f"Relay {i}"
        if st.session_state.relays[relay_key]:
            if st.button(f"🟢 {label}", key=f"{relay_key}_on"):
                st.session_state.mqtt_client.publish_command(i, False)
        else:
            if st.button(f"🔴 {label}", key=f"{relay_key}_off"):
                st.session_state.mqtt_client.publish_command(i, True)

# Sensor Data Display
st.divider()
st.subheader("📊 Sensor Data")

# Digital Inputs
with st.expander("Digital Inputs (D1-D16)", expanded=True):
    dig_cols = st.columns(4)
    for i in range(1, 17):
        with dig_cols[(i-1) % 4]:
            input_key = f"D{i}"
            state = "ON 🟢" if st.session_state.digital_inputs[input_key] else "OFF 🔴"
            st.metric(label=f"Digital {i}", value=state)

# Analog Inputs
with st.expander("Analog Inputs (A1-A16)", expanded=True):
    analog_cols = st.columns(4)
    for i in range(1, 17):
        with analog_cols[(i-1) % 4]:
            input_key = f"A{i}"
            value = st.session_state.analog_inputs[input_key]
            st.metric(label=f"Analog {i}", value=f"{value}%")

# Temperature Sensors
with st.expander("Temperature Sensors (T1-T5)", expanded=True):
    temp_cols = st.columns(5)
    for i in range(1, 6):
        with temp_cols[i-1]:
            temp_key = f"T{i}"
            value = st.session_state.temperature_sensors[temp_key]
            st.metric(label=f"Temp {i}", value=f"{value}°C")

# System Commands
st.divider()
if st.button("🔄 Refresh All Data"):
    st.session_state.mqtt_client.request_state()
    st.toast("Requested status update", icon="🔄")

# Auto-refresh
if st.checkbox("Auto-refresh (every 5 seconds)"):
    time.sleep(5)
    st.rerun()