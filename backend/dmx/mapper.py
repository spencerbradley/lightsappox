from models.device import DMXDevice
class MAPPER:
    def __init__(self):
        self.channels_in_order = []

    def set_channel_values(self, devices: list[DMXDevice]) -> None:
        self.channels_in_order = []
        sorted_devices = sorted(devices, key=lambda d: d.order)
        for device in sorted_devices:
            self.channels_in_order.extend(device.active_channels)

    def get_channel_values(self) -> list[int]:
        return self.channels_in_order

