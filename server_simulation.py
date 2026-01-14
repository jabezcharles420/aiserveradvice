import random
import time
import requests
import json
from dataclasses import dataclass, asdict

# Constants
METRICS_URL = "http://localhost:8000/metrics/update"
UPDATE_INTERVAL = 5

@dataclass
class ServerConfig:
    degradation_factor: float = 1.0

class Server:
    def __init__(self, server_id: int):
        self.server_id = server_id
        # Initialize with random values
        self.cpu_usage = random.uniform(10, 50)
        self.memory_usage = random.uniform(20, 60)
        self.disk_usage = random.uniform(30, 70)
        self.temperature = random.uniform(40, 60)
        self.health = 100.0
        self.status = "running"
        self.max_memory = 100.0
        self.max_cpu = 100.0
        self.target_temp = 40.0 # Ideal cooling target
        self.auto_restart = False
        
        # New Metrics
        self.net_up_speed = 0.0
        self.net_down_speed = 0.0
        self.power_watts = 150.0 # Base idle
        self.fan_rpm = 2000.0
        self.latency = 5.0
        
        # Config for simulation variety
        self.config = ServerConfig(degradation_factor=random.uniform(0.8, 1.5))
        
        # For disk growth simulation
        self.disk_growth_rate = random.uniform(0.1, 0.5)

    def clamp(self, value, min_val, max_val):
        return max(min_val, min(value, max_val))
        
    def sync_config(self, config):
        if not config:
            return
            
        if "status" in config:
            if self.status != config["status"]:
                print(f"Server {self.server_id}: Remote status change -> {config['status']}")
                self.status = config["status"]
                
        if "max_memory" in config:
            self.max_memory = float(config["max_memory"])
        if "max_cpu" in config:
            self.max_cpu = float(config["max_cpu"])
        if "target_temp" in config:
            self.target_temp = float(config["target_temp"])
        if "auto_restart" in config:
            self.auto_restart = bool(config["auto_restart"])

    def update(self):
        # Enforce limits
        if self.memory_usage > self.max_memory:
            self.memory_usage = self.max_memory
        if self.cpu_usage > self.max_cpu:
            self.cpu_usage = self.max_cpu

        if self.status == "terminated":
            return

        elif self.status == "exploded":
            self.health = 0
            self.temperature = 100
            self.power_watts = 0
            self.fan_rpm = 0

        elif self.status == "disconnected":
            # Server runs, but metrics might be stale/unsent (handled in main loop)
            # Power behaves normally
            pass

        elif self.status == "hibernated":
            self.cpu_usage = self.clamp(self.cpu_usage - 10, 0, self.max_cpu)
            self.memory_usage = self.clamp(self.memory_usage, 0, self.max_memory)
            self.temperature = self.clamp(self.temperature - 5, 20, 100)
            self.power_watts = 20.0 # Low power state
            self.fan_rpm = 500.0
            self.net_up_speed = 0.0
            self.net_down_speed = 0.0
            self.latency = 0.0
            
        elif self.status == "off":
            self.cpu_usage = 0
            self.temperature = self.clamp(self.temperature - 5, 20, 100)
            self.memory_usage = 0
            self.power_watts = 5.0 # Standby
            self.fan_rpm = 0.0
            self.net_up_speed = 0.0
            self.net_down_speed = 0.0
            self.latency = 0.0
            
            # Auto Restart Logic
            if self.auto_restart and self.health > 50:
                 if random.random() < 0.2: 
                     self.status = "running"
                     print(f"Server {self.server_id} AUTO-RESTARTED.")
            
        elif self.status == "running":
            # 1. CPU/Mem Fluctuations
            cpu_noise = random.uniform(-5, 10) * self.config.degradation_factor
            self.cpu_usage = self.clamp(self.cpu_usage + cpu_noise, 0, self.max_cpu)
            
            mem_noise = random.uniform(-2, 5) * self.config.degradation_factor
            self.memory_usage = self.clamp(self.memory_usage + mem_noise, 0, self.max_memory)

            # 2. Disk
            self.disk_usage = self.clamp(self.disk_usage + self.disk_growth_rate, 0, 100)

            # 3. Temperature 
            heat_gen = self.cpu_usage * 0.8
            cooling_power = (self.temperature - self.target_temp) * 0.3
            self.temperature = self.clamp(self.temperature + (heat_gen * 0.1) - cooling_power + random.uniform(-1, 1), 20, 100)

            # 4. New Metrics simulation
            # Network: correlated with cpu slightly
            base_net = self.cpu_usage * 2.0 
            self.net_up_speed = max(0, base_net + random.uniform(-20, 20))
            self.net_down_speed = max(0, base_net + random.uniform(-20, 100))
            
            # Power: correlated with cpu and fans
            power_load = (self.cpu_usage * 2.5) + (self.memory_usage * 0.5)
            self.power_watts = 100.0 + power_load + random.uniform(-5, 5)
            
            # Fans: correlated with temperature
            target_rpm = 1000 + (self.temperature * 50)
            self.fan_rpm = self.fan_rpm + (target_rpm - self.fan_rpm) * 0.1
            
            # Latency: increases with heavy load
            load_factor = (self.cpu_usage + self.memory_usage + self.net_down_speed/10) / 300.0
            self.latency = 10 + (load_factor * 100) + random.uniform(-5, 5)
            self.latency = max(1, self.latency)

            # 5. Health
            health_drop = 0
            if self.temperature > 85:
                health_drop += 2 * self.config.degradation_factor
            if self.disk_usage > 95:
                health_drop += 1 * self.config.degradation_factor
            if self.cpu_usage > 98:
                health_drop += 0.5
                
            self.health = self.clamp(self.health - health_drop, 0, 100)
            
            # Critical low health
            if self.health < 10:
                if random.random() < 0.1: 
                    self.status = "off"
                    print(f"Server {self.server_id} CRASHED (Low Health).")
            
            # Random crash
            if random.random() < 0.005: 
                self.status = "off"
                print(f"Server {self.server_id} STOPPED (Random Event).")

    def to_dict(self):
        return {
            "server_id": self.server_id,
            "cpu": round(self.cpu_usage, 2),
            "memory": round(self.memory_usage, 2),
            "disk": round(self.disk_usage, 2),
            "temperature": round(self.temperature, 2),
            "health": round(self.health, 2),
            "status": self.status,
            "max_memory": self.max_memory,
            "max_cpu": self.max_cpu,
            "target_temp": self.target_temp,
            "auto_restart": self.auto_restart,
            "net_up_speed": round(self.net_up_speed, 1),
            "net_down_speed": round(self.net_down_speed, 1),
            "power_watts": round(self.power_watts, 1),
            "fan_rpm": int(self.fan_rpm),
            "latency": round(self.latency, 1)
        }

def main():
    print("Initializing 10 fake servers...")
    servers = [Server(i) for i in range(1, 25)]
    
    # Intentionally start one as off
    servers[9].status = "off"

    while True:
        print(f"\n--- Update Cycle {time.strftime('%H:%M:%S')} ---")
        for server in servers:
            server.update()
            
            # Skip sending if disconnected
            if server.status == "disconnected":
                print(f"Server {server.server_id} is DISCONNECTED. Skipping update.")
                # Still checking for config in a real app would be impossible, but here we might skip it or simulate out-of-band
            
            payload = server.to_dict()
            
            try:
                # Set a short timeout so simulation doesn't hang if receiver is down
                response = requests.post(METRICS_URL, json=payload, timeout=1)
                
                if response.status_code == 200:
                    data = response.json()
                    if "config" in data:
                        server.sync_config(data["config"])
                
                print(f"Sent update for Server {server.server_id} | Health: {payload['health']} | Temp: {payload['temperature']}")
            except requests.exceptions.ConnectionError:
                 print(f"Server {server.server_id}: Failed to connect to {METRICS_URL}")
            except Exception as e:
                print(f"Server {server.server_id}: Error sending update - {e}")
        
        time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    main()
