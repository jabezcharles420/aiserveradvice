import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Server Monitoring Dashboard", layout="wide")

BACKEND_URL = "http://localhost:8000"

st.title("🖥️ Local Server Monitoring Dashboard")
st.caption("Reading data from local FastAPI backend")

def fetch_servers():
    try:
        r = requests.get(f"{BACKEND_URL}/servers", timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        return None

placeholder = st.empty()

while True:
    with placeholder.container():
        st.subheader("📊 Live Server Status")

        data = fetch_servers()

        if data is None:
            st.error("❌ Cannot connect to backend at http://localhost:8000")
            st.info("Make sure dummy_receiver.py is running.")
        elif len(data) == 0:
            st.warning("⚠️ No server data yet. Is the simulator running?")
        else:
            df = pd.DataFrame(data)

            # reorder columns if present
            cols = ["id", "status", "health", "cpu", "memory", "disk", "temperature"]
            existing_cols = [c for c in cols if c in df.columns]
            df = df[existing_cols]

            def color_health(val):
                if val > 70:
                    return "background-color: #c6f6d5"
                elif val > 40:
                    return "background-color: #fefcbf"
                else:
                    return "background-color: #fed7d7"

            st.dataframe(
                df.style.applymap(color_health, subset=["health"]),
                use_container_width=True,
                height=400
            )

        st.caption("Last updated: " + time.strftime("%H:%M:%S"))

    time.sleep(3)
