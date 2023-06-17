from typing import Optional
import adbutils
from TDTK.logger import Logger
import time
from pathlib import Path
logger = Logger(None)
thisPath = Path(__file__).parent
filesPath = thisPath / "files"

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
        type: Optional[str],
        file: Optional[str],
        timeout: Optional[int] = 2,
        overwrite: Optional[bool] = False,
    ) -> bool:
        logger.log(f"adb run type is {type}", type="debug")
        if not self.root():
            logger.log(f"Failed to restart adb as root!", type="plainFailure")
            return False
        if type == "app-install-priv":
            logger.log(f"Running install-app routine", type="debug")
            return self.run_app_install(priv=True, file=file, overwrite=overwrite)
        if type == "app-install":
            logger.log(f"Running install-app routine", type="debug")
            return self.run_app_install(file=file)
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

    def run_app_install(
        self,
        file: str,
        priv: Optional[bool] = False,
        overwrite: Optional[bool] = False,
    ):
        ret = self.remount()
        if not ret:
            logger.log(f"Failed to remount device as RW!", type="plainFailure")
            return False
        if priv:
            logger.log(f"Running install-app-priv routine", type="debug")
            self.run_app_install_priv(file, overwrite)
        else:
            logger.log(f"Running adb install now!", type="debug")
            self.device.install(str(filesPath / file), nolaunch=True, silent=True)
        return True

    def run_app_install_priv(
        self,
        file: str,
        overwrite: Optional[bool] = False,
    ):
        logger.log(f"In run_app_install_priv", type="debug")
        file = str(file)
        if not overwrite:
            logger.log(f"Not overwriting!", type="debug")
            command = f'[ -f /product/priv-app/{file.split(".")[0]}/{file} ]'
            logger.log(f"File check command is {command}", type="debug")
            ret = self.device.shell2(command)
            logger.log(f"Returncode for check command is {ret.returncode}", type="debug")
            if ret.returncode == 0:
                logger.log("App already on filesystem, skipping installation...", type="result")
                return True
        else:
            logger.log(f"Overwriting!", type="debug")
        ret = self.device.shell2(f'mkdir /product/priv-app/{file.split(".")[0]}')
        if not ret.returncode == 0:
            return False
        ret = self.device.shell2(f'mv /sdcard/TDTK/{file} /product/priv-app/{file.split(".")[0]}/')
        if not ret.returncode == 0:
            return False

    def _remount(self):
        return self.device.shell2("remount")

    def remount(self, bail: Optional[bool] = False):
        ret = self._remount()
        if ret == "inaccessible":
            return False
        if ret == "root":
            if bail:
                return False
            if not self.root():
                return False
            ret = self.remount(bail=True)
        return True

    def root(self):
        ret = self.device.root()
        if ret == "cannot run as root":
            return False
        return True

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
        try:
            ret = self.device.shell2(command)
        except:
            return 1
        return ret.returncode
