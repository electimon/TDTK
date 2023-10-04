import json
import os
import time
from pathlib import Path
from typing import Optional
from TDTK.logger import Logger
from TDTK.adb import ADB
from enum import Enum

logger = Logger(None)
adb = ADB()
thisPath = Path(__file__).parent

class ValidationResult(Enum):
    VALID = 0
    NOT_DICT = 1
    MISSING_COMMAND_OR_TYPE = 2
    MISSING_EXPECTED_OUTPUT = 3
    INVALID_FILE_FIELD = 4
    INVALID_DEPENDS_FIELD = 5

def is_valid_module(submodule):
    if not isinstance(submodule, dict):
        return ValidationResult.NOT_DICT
    if not submodule.get("command") and not submodule.get("type"):
        return ValidationResult.MISSING_COMMAND_OR_TYPE
    if submodule.get("expected") is None:
        return ValidationResult.MISSING_EXPECTED_OUTPUT
    if submodule.get("file") and not isinstance(submodule.get("file"), str):
        return ValidationResult.INVALID_FILE_FIELD
    if submodule.get("depends") and not isinstance(submodule.get("depends"), str):
        return ValidationResult.INVALID_DEPENDS_FIELD
    return ValidationResult.VALID

class Modules:
    def __init__(self):
        self.available_modules = {}
        self.load_modules()

    def load_module(self, filepath: Path):
        module_name = filepath.stem
        with open(filepath) as entry:
            submodules = {}
            try:
                module_data = json.load(entry)
            except:
                logger.log(f'Failed to load {filepath}, it has been skipped!', 'plainFailure')
                return
            for key in module_data:
                submodule = module_data[key]
                result = is_valid_module(submodule)
                case = {
                    ValidationResult.VALID: lambda: (
                        logger.log(f'Method "{key}" in {os.path.relpath(filepath)} has been validated!', "debug"),
                        submodules.update({key: SubModule(module_name, submodule)})
                    ),
                    ValidationResult.NOT_DICT: lambda: logger.log(f'Method "{key}" in {os.path.relpath(filepath)} is not a dict, it has been skipped!', "plainFailure"),
                    ValidationResult.MISSING_COMMAND_OR_TYPE: lambda: logger.log(f'Method "{key}" in {os.path.relpath(filepath)} is missing a command or type, it has been skipped!', "plainFailure"),
                    ValidationResult.MISSING_EXPECTED_OUTPUT: lambda: logger.log(f'Method "{key}" in {os.path.relpath(filepath)} is missing an expected output, it has been skipped!', "plainFailure"),
                    ValidationResult.INVALID_FILE_FIELD: lambda: logger.log(f'Invalid "file" field in method "{key}" of {os.path.relpath(filepath)}, it has been skipped!', "plainFailure"),
                    ValidationResult.INVALID_DEPENDS_FIELD: lambda: logger.log(f'Invalid "depends" field in method "{key}" of {os.path.relpath(filepath)}, it has been skipped!', "plainFailure")
                }
                result_func = case.get(result, lambda: None)
                result_func()
            container = filepath.stem if filepath.parent.stem.endswith('modules') else filepath.parent.stem + '.' + module_name
            if submodules:
                self.available_modules[container] = Module(self, module_name, submodules)

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

    def run(self, module_name: str, submodule_name: str, parameters: Optional[list[str]]):
        module = self.available_modules.get(module_name)
        if module:
            return module.run(submodule_name, parameters)
        else:
            logger.log(f'Module "{module_name}" not found!', "failure")
            return False

class SubModule:
    def __init__(self, name, data):
        self.__dict__.update(data)
        self.depends = data.get("depends")
        self.files = [Path(file) for file in data.get("files", [])]  # Store multiple files as a list of Paths
        self.parent_name = name

    def run(self, parameters: Optional[list[str]]):
        command = getattr(self, "command", None)
        check = getattr(self, "check", None)
        expected = getattr(self, "expected", None)
        timeout = getattr(self, "timeout", None)
        command_type = getattr(self, "type", None)
        overwrite = getattr(self, "overwrite", None)
        wait = getattr(self, "wait", None)
        logger.log(f'Command is "{command}", check is "{check}", expected is "{expected}", timeout is "{timeout}", wait is "{wait}"', "debug")
        if not self.push_files():
            return False
        ret = adb.run(
            command=command,
            check=check,
            expected=expected,
            parameters=parameters,
            timeout=timeout,
            command_type=command_type,
            files=self.files,
            overwrite=overwrite
        )
        if wait:
            logger.log(f'Waiting {wait} seconds for completion', "plainSpaced")
            time.sleep(wait)
        return ret

    def push_files(self):
        for file in self.files:
            file_path = thisPath / "files" / file
            if file_path.is_file():
                logger.log(f'Pushing file {file_path} to device!', "debug")
                ret = adb.push(file_path)
                if not ret > 0:
                    logger.log(f'Failed to push "{file_path}"!', 'plainFailure')
            else:
                logger.log(f'This module requires a file, "{file}", which was not found, skipping!', "plainFailure")
                return False
        return True

class Module:
    def __init__(self, modules, name, submodules):
        self.name = name
        self.modules = modules
        self.submodules = submodules

    def run(self, submodule_name: str, parameters: Optional[list[str]]):
        logger.log(f"Attempting to run {self.name}.{submodule_name}", "debug")
        submodule = self.get_submodule(submodule_name)
        if not submodule:
            logger.log(f'Submodule "{submodule_name}" not found!', "failure")
            return False
        if submodule.depends:
            depends = submodule.depends.split(".")
            if len(depends) < 2: # single word in depends, external module
                logger.log(f"{self.name}.{submodule_name} depends on {submodule.parent_name}.{submodule.depends}!", "debug")
                ret = self.run(submodule.depends, None)
                if not ret:
                    return ret
            if len(depends) > 1: # multi words in depends, local module
                logger.log(f"{self.name}.{submodule_name} depends on {submodule.depends}!", "debug")
                ret = self.modules.run(depends[0], depends[1], None)
                if not ret:
                    return ret
        return submodule.run(parameters)

    def get_submodule(self, name: str):
        return self.submodules.get(name, None)
