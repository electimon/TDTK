import adbutils, time
from TDTK.core.functions import wifi

class Tests:
    available_tests = [
        "test_bluetooth_pairing",
        "test_wifi_connection"
    ]
    
    def __init__(self, logger) -> None:
        self.logger = logger
        self.device: adbutils.AdbDevice = None
    
    def bluetooth_pairing(self, parameters):
        return 0
    
    def wifi_connection(self, parameters):
        ret = wifi.enable_wifi(self)
        if ret.returncode != 0:
            self.logger.log(f"Failed to turn on Wi-Fi!", type="debug")
            return ret
        if not wifi.is_enabled(self):
            self.logger.log(f"Failed to turn on Wi-Fi!", type="debug")
            return 1
        ret = wifi.connect(self, parameters)
        if ret != 0:
            self.logger.log(f"Failed to connect to Wi-Fi network!", type="debug")
            return ret
        if not wifi.is_connected(self):
            self.logger.log(f"Failed to connect to Wi-Fi network!", type="debug")
            return 1
        return 0
