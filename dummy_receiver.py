from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List, Optional

app = FastAPI(title="Local Server Monitor Backend")

SERVERS: Dict[int, dict] = {}
METRICS_LOG: List[dict] = []
SERVER_CONFIGS: Dict[int, dict] = {}

class MetricPayload(BaseModel):
    server_id: int
    cpu: float
    memory: float
    disk: float
    temperature: float
    health: float
    status: str
    max_memory: Optional[float] = 100.0
    max_cpu: Optional[float] = 100.0
    target_temp: Optional[float] = 40.0
    auto_restart: Optional[bool] = False
    
    # New metrics
    net_up_speed: Optional[float] = 0.0 # Mbps
    net_down_speed: Optional[float] = 0.0 # Mbps
    power_watts: Optional[float] = 0.0
    fan_rpm: Optional[float] = 0.0
    latency: Optional[float] = 0.0 # ms

class ControlPayload(BaseModel):
    server_id: int
    status: Optional[str] = None
    max_memory: Optional[float] = None
    max_cpu: Optional[float] = None
    target_temp: Optional[float] = None
    auto_restart: Optional[bool] = None

@app.post("/metrics/update")
def update_metrics(payload: MetricPayload):
    data = {
        "id": payload.server_id,
        "cpu": payload.cpu,
        "memory": payload.memory,
        "disk": payload.disk,
        "temperature": payload.temperature,
        "health": payload.health,
        "status": payload.status,
        "max_memory": payload.max_memory,
        "max_cpu": payload.max_cpu,
        "target_temp": payload.target_temp,
        "auto_restart": payload.auto_restart,
        
        "net_up_speed": payload.net_up_speed,
        "net_down_speed": payload.net_down_speed,
        "power_watts": payload.power_watts,
        "fan_rpm": payload.fan_rpm,
        "latency": payload.latency,
        
        "last_updated": datetime.now().isoformat()
    }
    
    SERVERS[payload.server_id] = data
    METRICS_LOG.append(data)

    # Return any pending config for this server
    config = SERVER_CONFIGS.get(payload.server_id, {})
    return {"status": "ok", "config": config}

@app.post("/control/update")
def update_control(payload: ControlPayload):
    if payload.server_id not in SERVER_CONFIGS:
        SERVER_CONFIGS[payload.server_id] = {}
    
    if payload.status:
        SERVER_CONFIGS[payload.server_id]["status"] = payload.status
    if payload.max_memory is not None:
        SERVER_CONFIGS[payload.server_id]["max_memory"] = payload.max_memory
    if payload.max_cpu is not None:
        SERVER_CONFIGS[payload.server_id]["max_cpu"] = payload.max_cpu
    if payload.target_temp is not None:
        SERVER_CONFIGS[payload.server_id]["target_temp"] = payload.target_temp
    if payload.auto_restart is not None:
        SERVER_CONFIGS[payload.server_id]["auto_restart"] = payload.auto_restart
        
    return {"status": "updated", "config": SERVER_CONFIGS[payload.server_id]}

@app.get("/metrics/history")
def get_metrics_history():
    return METRICS_LOG

@app.get("/servers")
def get_servers():
    return list(SERVERS.values())

@app.get("/metrics/{server_id}")
def get_metrics(server_id: int):
    return [m for m in METRICS_LOG if m["id"] == server_id]
