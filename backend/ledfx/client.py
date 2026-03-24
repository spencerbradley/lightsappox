# backend/ledfx/client.py
"""LedFx API Client"""

import json
import requests
from pydantic import TypeAdapter
from models.config import CONFIG
from models.ledfx_setting import LEDFXSetting


class LEDFXClient:
    def __init__(self, config_filepath: str, port: int = 8888):
        with open(config_filepath, "r") as f:
            data = json.load(f)
        adapter = TypeAdapter(CONFIG)
        config = adapter.validate_python(data)

        self.base_url = f"http://{config.server_host}:{port}/api"

    def get_scenes(self) -> dict:
        """Fetch all scenes from LedFx"""
        response = requests.get(f"{self.base_url}/scenes")
        response.raise_for_status()
        return response.json()

    def get_active_scene(self) -> str:
        """Get the currently active scene"""
        response = requests.get(f"{self.base_url}/scenes")
        response.raise_for_status()
        data = response.json()
        # LedFx returns scenes with "active" boolean - find the one that's active
        scenes = data.get("scenes", {})
        for scene_id, scene_data in scenes.items():
            if isinstance(scene_data, dict) and scene_data.get("active") is True:
                return scene_id
        return ""

    def set_active_scene(self, scene_id: str) -> None:
        """Activate a scene by ID"""
        # LedFx API: PUT /api/scenes with body {"id": scene_id, "action": "activate"}
        url = f"{self.base_url}/scenes"
        payload = {"id": scene_id, "action": "activate"}
        print(f"[LedFx] PUT request to: {url}")
        print(f"[LedFx] Payload: {payload}")
        response = requests.put(url, json=payload, timeout=5)
        print(f"[LedFx] Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"[LedFx] Response body: {response.text}")
        response.raise_for_status()

    def load_settings(self) -> list[LEDFXSetting]:
        """Fetch scenes and convert to LEDFXSetting objects"""
        scenes = self.get_scenes()
        settings = []
        for scene_id in scenes.get("scenes", {}).keys():
            settings.append(LEDFXSetting(id=scene_id))
        return settings

    def save_settings(self, filepath: str) -> None:
        """Fetch scenes and save as LEDFXSetting objects to JSON"""
        settings = self.load_settings()
        with open(filepath, "w") as f:
            json.dump([s.model_dump() for s in settings], f, indent=2)