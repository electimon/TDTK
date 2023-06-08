from typing import Optional
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
        
    def run(
        self,
        command: str,
        check: Optional[str],
        expected: str,
        parameters: Optional[list[str]],
        timeout: Optional[int] = 2,
    ) -> bool:
        if not timeout:
            timeout = 2
        if parameters:
            command = command + " " + " ".join(parameters)
        logger.log(f"Parameters: {parameters}", type="debug")
        ret = self.device.shell2(command)
        logger.log(f"Command: {command}", type="debug")
        logger.log(f"Command Output: {ret}", type="debug")
        if check:
            ret = self.check(check, expected, timeout)
            return ret
        return self.acceptable(ret, expected)
        
    def check(self,
              check: str,
              expected,
              timeout: Optional[int] = 2
    ):
        starttime = time.time()
        halfway_time = starttime + timeout / 2  # Calculate the halfway time
        if isinstance(expected, str):
            while time.time() < starttime + timeout:
                ret = self.device.shell(check)
                logger.log(f"Command: {check}", type="debug")
                logger.log(f"Command Output: {ret}", type="debug")
                if expected in ret:
                    return True
                # Check if halfway time has been reached
                if time.time() >= halfway_time:
                    logger.log("Still waiting for expected outcome...", type="ratelimited")
                time.sleep(0.2)  # Wait for a short duration before checking again
            return False
        ret = self.device.shell2(check)
        logger.log(f"Command: {check}", type="debug")
        logger.log(f"Command Output: {ret}", type="debug")
        return ret.returncode

    def acceptable(self, ret, expected) -> bool:
        if isinstance(ret, adbutils.ShellReturn): 
            if isinstance(expected, str):
                return expected in ret.output
            else:
                return expected == ret.returncode
        else:
            if isinstance(expected, str):
                return expected in ret
            else:
                return expected == ret        

    def push(self, fileName) -> int:
        ret = self.device.sync.push(fileName, f"/sdcard/TDTK/{fileName.stem}{fileName.suffix}")
        return ret
    
    def cleanup(self) -> int:
        command = "rm -rf /sdcard/TDTK"
        ret = self.device.shell2(command)
        return ret.returncode