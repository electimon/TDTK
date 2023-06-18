import json
import sys
from TDTK.logger import Logger
from TDTK.modules import Modules, Module
from TDTK.adb import ADB

class TestRunner:
    def __init__(self, args):
        self.args = args
        self.debug = args.debug
        self.logger = Logger(self)
        self.modules = Modules()
        self.adb = ADB()

    def start(self):
        self.setup_logger()
        self.detect_device()
        self.load_modules()
        self.load_test_suite()
        self.run_tests()
        self.finish()

    def setup_logger(self):
        self.logger.start()

    def detect_device(self):
        if self.adb.device:
            device_id = self.adb.device.serial
            self.logger.log(f"Device detected with ID: {device_id}", type="debug")
        else:
            self.logger.log("No devices detected, bailing!", type="plainFailure")
            self.finish()

    def load_modules(self):
        if len(self.modules.available_modules) == 0:
            self.logger.log("No modules were detected nor loaded!", "plainFailure")
            self.finish()

    def load_test_suite(self):
        with open(self.args.test_plan, "r") as test_plan_file:
            try:
                self.test_plan = json.load(test_plan_file)
            except json.JSONDecodeError:
                self.logger.log("Invalid test plan JSON provided, bailing!", type="fatal")
                self.finish()

    def run_tests(self):
        self.total_tests = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.errors = 0

        for test in self.test_plan:
            if self.validate_test(test):
                self.run_test(test)

    def validate_test(self, test: dict):
        name = test.get("test_name", None)
        module = test.get("module", None)
        self.logger.log(f'Running test: "{name}"', "section")

        if not name:
            self.logger.log("Test is missing the 'test_name' field!", type="failure")
            self.errors += 1
            return False
        if not module:
            self.logger.log(f"Test '{name}' is missing the 'module' field!", type="failure")
            self.errors += 1
            return False

        module_parts = module.split(".")
        if len(module_parts) < 2:
            self.logger.log(f"Test '{name}' has an invalid module format. Expected 'module.submodule' or 'category.module.submodule' format!", type="failure")
            self.errors += 1
            return False

        module_name = ".".join(module_parts[:-1])
        submodule_name = module_parts[-1]
        module = self.modules.available_modules.get(module_name)
        if not module:
            self.logger.log(f"Module '{module_name}' not found for test '{name}'!", type="failure")
            self.errors += 1
            return False

        submodule = module.get_submodule(submodule_name)
        if not submodule:
            self.logger.log(f"Submodule '{submodule_name}' not found in module '{module_name}' for test '{name}'!", type="failure")
            self.errors += 1
            return False

        self.logger.log(f"Test '{name}' in the test plan has been deemed valid!", type="debug")
        return True


    def run_test(self, test):
        test_name = test.get("test_name")
        module_name, submodule_name = test.get("module").rsplit(".", 1)
        module = self.modules.available_modules.get(module_name)

        if module:
            ret = module.run(submodule_name, test.get("parameters"))
            if ret is True:
                self.logger.log(f"Test \"{test_name}\" completed successfully.", type="result")
                self.tests_passed += 1
            else:
                self.logger.log(f"Test \"{test_name}\" has failed.", type="failure")
                self.tests_failed += 1
        else:
            self.logger.log(f'Module for "{test_name}" not found, skipped!', type="failure")
            self.errors += 1

        self.total_tests += 1

    def finish(self):
        self.logger.log_summary(self.total_tests, self.tests_passed, self.tests_failed, self.errors)
        if self.adb.device:
            self.adb.cleanup()  # Don't care if failed or not.
        sys.exit(1)
