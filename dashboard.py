import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
from server_advisor import analyze_server_data

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

def send_control(server_id, status=None, max_memory=None, max_cpu=None, target_temp=None, auto_restart=None):
    payload = {"server_id": server_id}
    if status: payload["status"] = status
    if max_memory is not None: payload["max_memory"] = max_memory
    if max_cpu is not None: payload["max_cpu"] = max_cpu
    if target_temp is not None: payload["target_temp"] = target_temp
    if auto_restart is not None: payload["auto_restart"] = auto_restart
        
    try:
        requests.post(f"{BACKEND_URL}/control/update", json=payload, timeout=2)
        return True
    except:
        return False

# Session state initialization
if "last_updated" not in st.session_state:
    st.session_state.last_updated = time.time()

# Main app logic (no infinite loop)
st.subheader("📊 Live Server Status")

data = fetch_servers()

if data is None:
    st.error("❌ Cannot connect to backend at http://localhost:8000")
    st.info("Make sure dummy_receiver.py is running.")
elif len(data) == 0:
    st.warning("⚠️ No server data yet. Is the simulator running?")
else:
    df = pd.DataFrame(data)
    
    # Ensure columns exist
    cols = ["id", "status", "health", "cpu", "memory", "disk", "temperature", "power_watts", "fan_rpm", "net_down_speed", "net_up_speed", "latency"]
    existing_cols = [c for c in cols if c in df.columns]
    df = df[existing_cols]

    # Style the dataframe
    def highlight_health(val):
        color = 'black' 
        if val > 80:
            bg = '#48bb78' # Green
        elif val > 50:
            bg = '#ecc94b' # Yellow
        else:
            bg = '#f56565' # Red
        return f'background-color: {bg}; color: {color}'

    st.dataframe(
        df.style.map(highlight_health, subset=["health"])
          .format({
              "cpu": "{:.1f}%", 
              "memory": "{:.1f}", 
              "disk": "{:.1f}%", 
              "temperature": "{:.1f}°C",
              "power_watts": "{:.0f}W",
              "fan_rpm": "{:.0f}",
              "latency": "{:.0f}ms",
              "net_down_speed": "{:.1f} Mbps",
              "net_up_speed": "{:.1f} Mbps"
          }),
        use_container_width=True,
        height=400,
        hide_index=True
    )
    
    st.divider()
    st.subheader("🛠️ Control Panel")
    
    # 4 columns for selection and main toggle
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        ids = sorted(df["id"].unique()) if not df.empty else []
        if ids:
            selected_id = st.selectbox("Select Server ID", options=ids)
            
            # Get current values for selected server
            current_server = df[df["id"] == selected_id].iloc[0]
            
            current_status = current_server["status"]
            current_max_mem = float(current_server.get("max_memory", 100))
            current_max_cpu = float(current_server.get("max_cpu", 100))
            current_target_temp = float(current_server.get("target_temp", 40))
            current_auto_restart = bool(current_server.get("auto_restart", False))
        else:
            selected_id = None

    if selected_id is not None:
        with c2:
            status_opts = ["running", "off", "hibernated", "disconnected"]
            idx = status_opts.index(current_status) if current_status in status_opts else 0
            new_status = st.selectbox("Set Status", status_opts, index=idx)
            
            new_auto_restart = st.toggle("Enable Auto-Restart", value=current_auto_restart)
        
        with c3:
            new_max_mem = st.number_input("Max Memory Limit", min_value=10.0, max_value=100.0, value=current_max_mem)
            new_max_cpu = st.number_input("Max CPU Limit", min_value=10.0, max_value=100.0, value=current_max_cpu)

        with c4:
            new_target_temp = st.slider("Target Temp (°C)", min_value=20.0, max_value=90.0, value=current_target_temp)
            
            st.write("") 
            if st.button("Update Configuration", type="primary"):
                if send_control(int(selected_id), new_status, new_max_mem, new_max_cpu, new_target_temp, new_auto_restart):
                    st.success(f"Updated Server {selected_id}!")
                    time.sleep(1.0) 
                    st.rerun() 
                else:
                    st.error("Failed to update.")

    st.divider()
    st.subheader("🤖 AI Expert Advisor & Reports")
    
    if selected_id:
        st.write(f"Analying Server **{selected_id}**...")
        
        c_adv1, c_adv2 = st.columns([1, 2])
        
        with c_adv1:
            if st.button("🧠 Generate AI Advice"):
                with st.spinner("Fetching history and consulting DeepSeek AI..."):
                    # 1. Fetch History
                    try:
                        hist_r = requests.get(f"{BACKEND_URL}/metrics/history", timeout=5)
                        if hist_r.status_code == 200:
                            full_hist_data = hist_r.json()
                            full_df = pd.DataFrame(full_hist_data)
                            
                            # Filter for this server
                            srv_hist_df = full_df[full_df["id"] == selected_id].copy()
                            # Rename 'id' to 'server_id' to match advisor expectation or just ensure consistency
                            srv_hist_df = srv_hist_df.rename(columns={"id": "server_id", "last_updated": "timestamp"})
                            
                            if not srv_hist_df.empty:
                                # Run Advisor
                                advice = analyze_server_data(selected_id, srv_hist_df)
                                st.session_state[f"advice_{selected_id}"] = advice
                                st.session_state[f"report_df_{selected_id}"] = srv_hist_df
                                st.success("Advice Generated!")
                            else:
                                st.warning("Not enough history for this server in backend memory.")
                        else:
                            st.error("Failed to fetch history from backend.")
                    except Exception as e:
                        st.error(f"Error: {e}")

        with c_adv2:
            advice_key = f"advice_{selected_id}"
            if advice_key in st.session_state:
                advice_text = st.session_state[advice_key]
                st.info(advice_text)
                
                # Prepare Download
                report_content = f"SERVER {selected_id} DIAGNOSTIC REPORT\n"
                report_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                report_content += "="*50 + "\n\n"
                report_content += "Processing Model: DeepSeek-R1-Free\n\n"
                report_content += "AI EXPERT ADVICE:\n"
                report_content += advice_text + "\n\n"
                report_content += "="*50 + "\n"
                report_content += "RAW DATA (Last 50 entries):\n"
                
                # Append data CSV style
                df_to_save = st.session_state[f"report_df_{selected_id}"]
                report_content += df_to_save.tail(50).to_csv(index=False)
                
                st.download_button(
                    label="📄 Download Diagnostic Report",
                    data=report_content,
                    file_name=f"server_{selected_id}_report.txt",
                    mime="text/plain"
                )
    else:
        st.info("Select a server above to enable the advisor.")

st.caption("Last updated: " + time.strftime("%H:%M:%S"))

# Auto-refresh logic
time.sleep(2)
st.rerun()
