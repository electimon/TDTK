import json
import os
from pathlib import Path
from TDTK.logger import Logger
from TDTK.adb import ADB

# Get the logger instance
logger = Logger(None)
# Get the ADB instance
adb = ADB()

def is_valid_module(submodule):
    if not isinstance(submodule, dict):
        return 1
    if not submodule.get("command", None):
        return 2
    if not submodule.get("expected", None):
        return 3
    return 0

class Modules:
    def __init__(self):
        self.available_modules = {}
        self.load_modules()

    def load_module(self, filepath):
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
            container = os.path.basename(os.path.dirname(filepath))
            if len(submodules) > 0:
                if "modules" in container:
                    self.available_modules[Path(filepath).stem] = Module(submodules)
                else:
                    self.available_modules[f"{container}.{Path(filepath).stem}"] = Module(submodules)

    def load_modules(self, dir=None):
        if not dir:
            dir = Path(__file__).parent / "modules"
        if not Path(dir).is_dir():
            return
        for entry in os.scandir(dir):
            if entry.is_file() and entry.name.endswith('.json'):
                logger.log(f'Scanning file {entry.name} for modules.', "debug")
                self.load_module(os.path.join(dir, entry.name))
            elif entry.is_dir():
                self.load_modules(entry.path)
        logger.log(f"Available modules, {self.available_modules}", "debug")

class SubModule:
    def __init__(self, data):
        self.__dict__.update(data)
        self.depends = data.get("depends")
    
    def run(self, parameters):
        logger.log(f'command is "{self.__dict__.get("command")}", check is "{self.__dict__.get("check")}", expected is "{self.__dict__.get("expected")}", timeout is "{self.__dict__.get("timeout")}"', "debug")
        ret = adb.run(self.__dict__.get("command"), self.__dict__.get("check"), self.__dict__.get("expected"), parameters)
        return ret

class Module:
    def __init__(self, submodules):
        self.submodules = submodules
    
    def run(self, submodule_name, parameters):
        logger.log(f"Attempting to run {submodule_name}", "debug")
        submodule = self.get_submodule(submodule_name)
        if submodule:
            if submodule.depends:
                if len(submodule.depends.split(".")) < 2:
                    ret = self.run(submodule.depends, None)
                    if not ret:
                        return ret 
            if submodule.run(parameters):
                return True
            else:
                return False
    
    def get_submodule(self, name):
        return self.submodules.get(name, None)