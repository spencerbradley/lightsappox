from backend.models.device import DMXDevice
from backend.models.dmx_presets import DMXPreset
class MAPPER:
    def __init__(self):
        self.channels_in_order = list[int]


    def create_list(self) -> list[int]:
        self.channels_in_order = [1] *