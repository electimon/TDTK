import adbutils
from TDTK.logger import Logger
import time
logger = Logger(None)

class ADB:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        self.adb_client = adbutils.AdbClient(host="127.0.0.1", port=5037)
        if len(self.adb_client.device_list()) > 0:
            self.device = self.adb_client.device_list()[0]
        else:
            self.device = None
        
    def run(self, command, check, expected, parameters):
        if parameters:
            command = command + " " + " ".join(parameters)
        logger.log(f"Parameters: {parameters}", type="debug")
        ret = self.device.shell2(command)
        logger.log(f"Command: {command}", type="debug")
        logger.log(f"Command Output: {ret}", type="debug")
        if check:
            ret = self.check(check, expected)
        if isinstance(ret, bool):
            return ret
        return ret.returncode
        
    def check(self, check, expected):
        starttime = time.time()
        if isinstance(expected, str):
            while time.time() < starttime + 10:
                ret = self.device.shell(check)
                logger.log(f"Command: {check}", type="debug")
                logger.log(f"Command Output: {ret}", type="debug")  
                if expected in ret:
                    return True
                time.sleep(0.2)  # Wait for a short duration before checking again
            return False
        ret = self.device.shell2(check)
        logger.log(f"Command: {check}", type="debug")
        logger.log(f"Command Output: {ret}", type="debug")
        return ret.returncode