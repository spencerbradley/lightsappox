#backend/models/config.json.py
"""Config Page"""
from pydantic import BaseModel

class CONFIG(BaseModel):
    id: str
    total_channels: int
    IP: str
    sacn_port: int
    priority: int
    universe: int
    server_host: str
    server_port: int
    ai_mode_enabled: bool = False

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "config1",
                "total_channels": 1,
                "IP": "192.168.0.177",
                "priority": 1,
                "universe": 1,
                "server_host": "127.0.0.1",
                "server_port": 8000,
                "sacn_port": 5568,
            }
        }
    }
