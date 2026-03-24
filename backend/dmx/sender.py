import json
import time

from pydantic import TypeAdapter

from models.config import CONFIG
from models.device import DMXDevice
from models.storage import load_optional
from routes.data import get_data_dir
from dmx.frame import DMXFrame
from dmx.mapper import MAPPER
import sacn

# Patch sacn so unreachable DMX host doesn't kill the send thread (WinError 10065, etc.)
_sacn_send_error_last_log = 0.0
_SACN_ERROR_LOG_INTERVAL = 10.0


def _send_packet_guarded(self, data: bytearray, destination: str) -> None:
    """Wrap send_packet to catch OSError (unreachable host) and log instead of raising."""
    global _sacn_send_error_last_log
    try:
        from sacn.sending.sender_socket_base import DEFAULT_PORT  # 5568
        data_raw = bytearray(data)
        self._socket.sendto(data_raw, (destination, DEFAULT_PORT))
    except OSError as e:
        now = time.time()
        if now - _sacn_send_error_last_log >= _SACN_ERROR_LOG_INTERVAL:
            print(f"[DMX] sACN send failed (destination unreachable?): {e}")
            _sacn_send_error_last_log = now


def _patch_sacn_send():
    try:
        from sacn.sending import sender_socket_udp
        sender_socket_udp.SenderSocketUDP.send_packet = _send_packet_guarded
    except Exception:
        pass


class SENDER:
    """Simple DMX sACN sender that only sends live data from devices.json."""

    def __init__(self, config_filepath: str):
        with open(config_filepath, "r") as f:
            data = json.load(f)
        adapter = TypeAdapter(CONFIG)
        config = adapter.validate_python(data)

        self.IP = config.IP
        self.priority = config.priority
        self.sacn_port = config.sacn_port
        self.universe = config.universe

        _patch_sacn_send()
        # Initialize sacn sender (default fps / internal throttling)
        self.sender = sacn.sACNsender(source_name="LightsApp")
        self.sender.start()
        self.sender.activate_output(self.universe)
        self.sender[self.universe].destination = self.IP
        self.sender[self.universe].multicast = False
        self.sender[self.universe].priority = self.priority

        self.active_frame = DMXFrame()

    def stop(self) -> None:
        self.sender.stop()

    def send(self) -> None:
        """Send current DMX values based solely on devices.json."""
        try:
            mapper = MAPPER()
            data_dir = get_data_dir()
            devices = load_optional(str(data_dir / "devices.json"), DMXDevice)
            mapper.set_channel_values(devices)
            channel_values = mapper.get_channel_values()
            self.active_frame.set_values(channel_values)

            dmx_values = list(self.active_frame.get_values())
            # Ensure exactly 512 channels
            if len(dmx_values) < 512:
                dmx_values.extend([0] * (512 - len(dmx_values)))
            elif len(dmx_values) > 512:
                dmx_values = dmx_values[:512]

            self.sender[self.universe].dmx_data = tuple(dmx_values)
        except Exception as e:
            print(f"[DMX] Error in send(): {e}")
            import traceback
            traceback.print_exc()

