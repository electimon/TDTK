import json
import os
from pathlib import Path
from typing import Optional
from TDTK.logger import Logger
from TDTK.adb import ADB

logger = Logger(None)
adb = ADB()
thisPath = Path(__file__).parent

def is_valid_module(submodule):
    if not isinstance(submodule, dict):
        return 1
    if not submodule.get("command") and not submodule.get("type"):
        return 2
    if submodule.get("expected") is None:
        return 3
    return 0

class Modules:
    def __init__(self):
        self.available_modules = {}
        self.load_modules()

    def load_module(self, filepath: Path):
        with open(filepath) as entry:
            submodules = {}
            module_data = json.load(entry)
            for key in module_data:
                submodule = module_data[key]
                result = is_valid_module(submodule)
                case = {
                    0: lambda: (
                        logger.log(f'Method "{key}" in {os.path.relpath(filepath)} has been validated!', "debug"),
                        submodules.update({key: SubModule(submodule)})
                    ),
                    1: lambda: logger.log(f'Method "{key}" in {os.path.relpath(filepath)} is not a dict, it has been skipped!', "plainFailure"),
                    2: lambda: logger.log(f'Method "{key}" in {os.path.relpath(filepath)} is missing a command, it has been skipped!', "plainFailure"),
                    3: lambda: logger.log(f'Method "{key}" in {os.path.relpath(filepath)} is missing an expected output, it has been skipped!', "plainFailure")
                }
                result_func = case.get(result, lambda: None)
                result_func()
            container = filepath.stem if filepath.parent.stem.endswith('modules') else filepath.parent.stem + '.' + filepath.stem
            if submodules:
                self.available_modules[container] = Module(submodules)

    def load_modules(self, dir: Path = None):
        if not dir:
            dir = thisPath / "modules"
        if not dir.is_dir():
            return
        for entry in dir.iterdir():
            if entry.is_file() and entry.name.endswith('.json'):
                logger.log(f'Scanning file {entry.name} for modules.', "debug")
                self.load_module(entry)
            elif entry.is_dir():
                self.load_modules(entry)
        logger.log(f"Available modules, {self.available_modules}", "debug")

class SubModule:
    def __init__(self, data):
        self.__dict__.update(data)
        self.depends = data.get("depends")
        self.file = Path(data.get("file")) if data.get("file") else None
    
    def run(self, parameters: Optional[list[str]]):
        logger.log(f'Command is "{self.__dict__.get("command")}", check is "{self.__dict__.get("check")}", expected is "{self.__dict__.get("expected")}", timeout is "{self.__dict__.get("timeout")}"', "debug")
        if self.file:
            filePath = thisPath / "files" / self.file
            if filePath.is_file():
                logger.log(f'Pushing file {filePath} to device!', "debug")
                ret = adb.push(filePath)
                if not ret > 0: # This function from adbutils returns file size of what it pushed.
                    logger.log(f'Failed to push "{filePath}"!', 'plainFailure')
            else:
                logger.log(f'This module requires a file, "{self.file}", which was not found, skipping!', "plainFailure")
                return False
        ret = adb.run(command=self.__dict__.get("command"), check=self.__dict__.get("check"), expected=self.__dict__.get("expected"), parameters=parameters, timeout=self.__dict__.get("timeout"), type=self.__dict__.get("type"), file=self.__dict__.get("file"), overwrite=self.__dict__.get("overwrite"))
        return ret

class Module:
    def __init__(self, submodules):
        self.submodules = submodules
    
    def run(self, submodule_name: str, parameters: Optional[list[str]]):
        logger.log(f"Attempting to run {submodule_name}", "debug")
        submodule = self.get_submodule(submodule_name)
        if not submodule:
            logger.log(f'Submodule "{submodule_name}" not found!', "failure")
            return False
        if submodule.depends and len(submodule.depends.split(".")) < 2:
            ret = self.run(submodule.depends, None)
            if not ret:
                return ret
        return submodule.run(parameters)
    
    def get_submodule(self, name: str):
        return self.submodules.get(name, None)
