import csv
import random
from datetime import datetime, timedelta
from server_simulation import Server

def generate_history():
    print("Generating historic data...")
    servers = [Server(i) for i in range(1, 11)]
    
    # Start time: 1000 steps * 5 seconds ago
    start_time = datetime.now() - timedelta(seconds=5000)
    
    history_data = []
    
    # Header
    fieldnames = [
        "timestamp", "server_id", "cpu", "memory", "disk", 
        "temperature", "health", "status", "max_memory", 
        "max_cpu", "target_temp", "auto_restart",
        "net_up_speed", "net_down_speed", "power_watts", "fan_rpm", "latency"
    ]
    
    for step in range(1000):
        current_time = start_time + timedelta(seconds=step*5)
        
        for server in servers:
            server.update()
            data = server.to_dict()
            data["timestamp"] = current_time.strftime("%Y-%m-%d %H:%M:%S")
            history_data.append(data)
            
    # Write to CSV
    filename = "server_history.csv"
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(history_data)
        
    print(f"Successfully generated {len(history_data)} records to {filename}")

if __name__ == "__main__":
    generate_history()
