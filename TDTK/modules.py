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

    def load_modules(self):
        module_dir = os.path.join(os.path.dirname(__file__), "modules")
        for file in os.scandir(module_dir):
            if file.is_file() and file.name.endswith('.json'):
                filepath = os.path.join(module_dir, file.name)
                with open(filepath) as file:
                    submodules = {}
                    module_data = json.load(file)
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
                    if len(submodules) > 1:
                        self.available_modules.update({Path(filepath).stem: (Module(submodules))})

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