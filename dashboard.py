import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Server Monitoring Dashboard", layout="wide")

BACKEND_URL = "http://localhost:8000"

st.title("🖥️ Fake Server Monitoring System")

st.markdown("Live view of 10 simulated servers. Auto-refreshes every 5 seconds.")

# Auto refresh every 5 seconds
st_autorefresh = st.empty()

def fetch_servers():
    try:
        r = requests.get(f"{BACKEND_URL}/servers", timeout=2)
        if r.status_code == 200:
            return r.json()
    except:
        return None

placeholder = st.empty()

while True:
    with placeholder.container():
        st.subheader("📊 Server Status")

        data = fetch_servers()

        if data is None:
            st.error("❌ Cannot connect to backend. Is FastAPI running?")
        else:
            df = pd.DataFrame(data)

            # Reorder columns
            if not df.empty:
                df = df[["id", "status", "health", "cpu", "memory", "disk", "temperature"]]

                # Color health
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

    time.sleep(5)
