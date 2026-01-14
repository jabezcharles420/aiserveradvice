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
        
        # Config for simulation variety
        self.config = ServerConfig(degradation_factor=random.uniform(0.8, 1.5))
        
        # For disk growth simulation
        self.disk_growth_rate = random.uniform(0.1, 0.5)

    def clamp(self, value, min_val, max_val):
        return max(min_val, min(value, max_val))

    def update(self):
        if self.status == "terminated":
            return

        elif self.status == "stopped":
            # Cooldown
            self.cpu_usage = self.clamp(self.cpu_usage - 5, 0, 100)
            self.temperature = self.clamp(self.temperature - 2, 30, 100)
            # Memory might stay allocated or drop, let's say it stays for now or drops slowly
            self.memory_usage = self.clamp(self.memory_usage - 1, 0, 100)
            
            # Chance to restart
            if random.random() < 0.05:
                self.status = "running"
                print(f"Server {self.server_id} RESTARTED.")

        elif self.status == "running":
            # 1. Fluctuate CPU and Memory
            cpu_noise = random.uniform(-5, 10) * self.config.degradation_factor
            self.cpu_usage = self.clamp(self.cpu_usage + cpu_noise, 0, 100)
            
            mem_noise = random.uniform(-2, 5) * self.config.degradation_factor
            self.memory_usage = self.clamp(self.memory_usage + mem_noise, 0, 100)

            # 2. Disk slowly increases
            self.disk_usage = self.clamp(self.disk_usage + self.disk_growth_rate, 0, 100)

            # 3. Temperature increases with CPU
            # Target temp based on CPU load
            target_temp = 40 + (self.cpu_usage * 0.6) 
            temp_change = (target_temp - self.temperature) * 0.2
            self.temperature = self.clamp(self.temperature + temp_change + random.uniform(-1, 1), 30, 100)

            # 4. Health calculations
            health_drop = 0
            if self.temperature > 80:
                health_drop += 2 * self.config.degradation_factor
            if self.disk_usage > 90:
                health_drop += 1 * self.config.degradation_factor
            if self.cpu_usage > 95:
                health_drop += 1
                
            self.health = self.clamp(self.health - health_drop, 0, 100)
            
            # Identify critical failure
            if self.health < 10:
                if random.random() < 0.1: # 10% chance to crash if critical
                    self.status = "stopped"
                    print(f"Server {self.server_id} CRASHED (Low Health).")
            
            # Random events
            if random.random() < 0.01: # 1% chance to randomly stop
                self.status = "stopped"
                print(f"Server {self.server_id} STOPPED (Random Event).")

    def to_dict(self):
        return {
            "server_id": self.server_id,
            "cpu": round(self.cpu_usage, 2),
            "memory": round(self.memory_usage, 2),
            "disk": round(self.disk_usage, 2),
            "temperature": round(self.temperature, 2),
            "health": round(self.health, 2),
            "status": self.status
        }

def main():
    print("Initializing 10 fake servers...")
    servers = [Server(i) for i in range(1, 11)]
    
    # Intentionally start one as stopped
    servers[9].status = "stopped"

    while True:
        print(f"\n--- Update Cycle {time.strftime('%H:%M:%S')} ---")
        for server in servers:
            server.update()
            payload = server.to_dict()
            
            try:
                # Set a short timeout so simulation doesn't hang if receiver is down
                requests.post(METRICS_URL, json=payload, timeout=1)
                print(f"Sent update for Server {server.server_id} | Health: {payload['health']} | Temp: {payload['temperature']}")
            except requests.exceptions.ConnectionError:
                 print(f"Server {server.server_id}: Failed to connect to {METRICS_URL}")
            except Exception as e:
                print(f"Server {server.server_id}: Error sending update - {e}")
        
        time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    main()
