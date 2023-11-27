import os
from typing import Optional
import adbutils
from TDTK.core.logger import Logger
from TDTK.core.indicator import Indicator
import time
from pathlib import Path
logger = Logger(None)
thisPath = Path(__file__).parent
filesPath = thisPath / "files"

class ADB:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        cls._instance = cls._instance or object.__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        self.adb_client = adbutils.AdbClient(host="127.0.0.1", port=5037)
        devices = self.adb_client.device_list()
        self.device = devices[0] if devices else None
        self.indicator = Indicator()
        
    def run(
        self,
        command: Optional[str],
        check: Optional[str],
        expected: str,
        parameters: Optional[list[str]],
        command_type: Optional[str],
        files: Optional[list[str]],
        timeout: Optional[int] = 2,
        overwrite: Optional[bool] = False,
        silent: Optional[bool] = True,
        repeat: Optional[int] = 0,
    ) -> bool:
        logger.log(f"adb run type is {command_type}", type="debug")
        if not self.root():
            logger.log(f"Failed to restart adb as root!", type="plainFailure")
            return False
        if command_type == "app-install-priv":
            logger.log(f"Running install-app-priv routine", type="debug")
            return self.run_app_install_priv(files[0], files[1:], overwrite)
        if command_type == "app-install":
            logger.log(f"Running install-app routine, files are {files}", type="debug")
            return self.run_app_install(files[0])
        if command_type == "push-exec":
            logger.log(f"Running push-exec routine, files are {files}", type="debug")
            return self.run_push_exec(files)
        if not timeout:
            timeout = 2
        if not command:
            logger.log(f"No command found, skipping!", type="plainFailure")
            return False
        if parameters:
            command = f"{command} {' '.join(parameters)}"
        logger.log(f"Running command: {command}", type="debug")
        logger.log(f"Parameters: {parameters}", type="debug")
        self.indicator.start()
        if repeat:
            for _ in range(repeat):
                logger.log(f"Command: {command}, in iteration!", type="debug")
                ret = self.run_command(command, check, expected, timeout, silent)
                if not ret:
                    return False
                return ret
        else:
            return self.run_command(command, check, expected, timeout, silent)

    def run_command(self, command: str, check: str, expected: str, timeout: int, silent: bool) -> bool:
        ret = self.device.shell2(command)
        if not silent:
            logger.log(f"Command Output: {ret.output if ret.output else ret.returncode}", type="summarySpaced")
        else:
            logger.log(f"Command Output: {ret.output if ret.output else ret.returncode}", type="debug")
        if check:
            ret = self.check(check, expected, timeout)
            return ret
        self.indicator.stop()
        return self.acceptable(ret, expected)

    def run_push_exec(self, files: list[str]) -> bool:
        for file in files:
            if self.push(filesPath / file, f"/data/local/tmp/{file}") <= 0:
                logger.log(f"Failed to push file {file}!", type="plainFailure")
                return False
        logger.log(f"Pushed files successfully!", type="debug")
        return True

    def run_app_install(
        self,
        file: str,
    ) -> bool:
        ret = self.remount()
        if not ret:
            return False
        else:
            logger.log(f"Running adb install now!", type="debug")
            self.device.install(str(filesPath / file), nolaunch=True, silent=True)
        return True

    def run_app_install_priv(
        self,
        apk_name: str,
        additional_files: list[str],
        overwrite: Optional[bool] = False,
    ):
        logger.log(f"In run_app_install_priv", type="debug")
        ret = self.remount()
        if not ret:
            return False
        apk_name = str(apk_name)
        if not overwrite:
            for file in additional_files:
                file = str(file)
                logger.log(f"Additional file found! {file}", type="debug")
                if "privapp-permissions" in file:
                    if self.check_file_existence(f'/product/etc/permissions/{file}'):
                        continue
                    else:
                        if not self.move_file(file, f'/product/etc/permissions/{file}', create_path=False):
                            return False
                if "default-permissions" in file:
                    if self.check_file_existence(f'/product/etc/default-permissions/{file}'):
                        continue
                    else:
                        if not self.move_file(file, f'/product/etc/default-permissions/{file}', create_path=False):
                            return False                   
            if self.check_file_existence(f'/product/priv-app/{apk_name.split(".")[0]}/{apk_name}'):
                return True
        else:
            for file in additional_files:
                file = str(file)
                if "default-permissions" in file:
                    if not self.move_file(file, f'/product/etc/default-permissions/{file}', create_path=False):
                        return False
                if "privapp-permissions" in file:
                    if not self.move_file(file, f'/product/etc/permissions/{file}', create_path=False):
                        return False
            logger.log(f"Overwriting!", type="debug")

        if not self.move_file(apk_name, f'/product/priv-app/{apk_name.split(".")[0]}/'):
            return False
        return True

    def move_file(self, source_path: str, destination_path: str, create_path: Optional[bool] = True) -> bool:
        if create_path:
            ret = self.device.shell2(f'mkdir -p {destination_path} && chmod 755 {destination_path}')
            logger.log(f"Creating directory {destination_path} with 755 permissions", type="debug")
            if ret.returncode != 0:
                return False
        logger.log(f"Moving file /sdcard/TDTK/{source_path} to {destination_path}", type="debug")
        ret = self.device.shell2(f'mv /sdcard/TDTK/{source_path} {destination_path}')
        if ret.returncode != 0:
            logger.log(f"Failed to move file /sdcard/TDTK/{source_path} to {destination_path}, output: {ret.output}", type="plainFailure")
            return False
        root, ext = os.path.splitext(destination_path)
        if not ext:
            destination_path = f"{destination_path}{source_path}"
        ret = self.device.shell2(f'chown root:root {destination_path} && chmod 644 {destination_path}')
        if ret.returncode != 0:
            logger.log(f"Failed to change ownership of {destination_path}, output: {ret.output}", type="plainFailure")
            return False
        logger.log(f"Changing ownership for file {destination_path}", type="debug")
        return True

    def check_files_existence(self, file_paths: list[str]) -> bool:
        for file_path in file_paths:
            if not self.check_file_existence(file_path):
                return False
        return True

    def check_file_existence(self, file_path: str) -> bool:
        command = f'[ -f {file_path} ]'
        logger.log(f"File check command is {command}", type="debug")
        ret = self.device.shell2(command)
        logger.log(f"Return code for check command is {ret.returncode}", type="debug")
        if ret.returncode == 0:
            logger.log(f'File {file_path} already exists on the device, skipping...', type="result")
            return True
        return False

    def remount(self, bail: Optional[bool] = False) -> bool:
        ret = self.device.shell2("remount")
        if ret == "inaccessible":
            logger.log(f"Failed to remount device as RW!", type="plainFailure")
            return False
        if ret == "root":
            if bail:
                logger.log(f"Failed to remount device as RW!", type="plainFailure")
                return False
            if not self.root():
                logger.log(f"Failed to remount device as RW!", type="plainFailure")
                return False
            ret = self.remount(bail=True)
        return True

    def root(self) -> bool:
        ret = self.device.root()
        if ret == "cannot run as root":
            return False
        return True

    def check(
        self,
        check: str,
        expected: str,
        timeout: Optional[int] = 2,
    ) -> bool:
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
        logger.log(f"Command Output: {ret.output}", type="debug")
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

    def push(self, file_name, dest=None) -> int:
        logger.log(f"Pushing file {file_name} to {dest}", type="debug")
        if not dest:
            ret = self.device.sync.push(
                file_name,
                f"/sdcard/TDTK/{dest}/{file_name.stem}{file_name.suffix}"
            )
        else:
            ret = self.device.sync.push(
                file_name,
                dest
            )
        return ret
    
    def cleanup(self) -> int:
        command = "rm -rf /sdcard/TDTK"
        try:
            ret = self.device.shell2(command)
        except:
            return 1
        return ret.returncode
