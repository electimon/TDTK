import json
from TDTK.logger import Logger
from TDTK.modules import Modules
from TDTK.adb import ADB

class TestRunner:
    def __init__(self, args) -> None:
        if not args or not args.test_plan :
            return
        self.test_plan = args.test_plan
        self.debug = args.debug
        self.total_tests = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.errors = 0
        self.logger = Logger(self)
        self.modules = Modules()
        if len(self.modules.available_modules) == 0:
            self.logger.log("No modules were detected nor loaded!", "plainFailure")
            self.errors += 1
        self.adb = ADB()
        
    def start(self): 
        if self.adb.device:
            device_id = self.adb.device.serial
            self.logger.log(f'Device detected with ID: {device_id}', type="debug")
        else:
            self.logger.log("No devices detected, bailing!", type="plainFailure")
            self.errors += 1
            self.finish()
            return
        
        # Output current testing information
        self.logger.start()
        
        # Make sure the device is in root mode
        self.adb.device.root()
        
        # Load the test suite from the JSON file
        with open(self.test_plan, "r") as test_plan_file:
            try:
                self.test_plan = json.load(test_plan_file)
            except json.JSONDecodeError:
                self.logger.log("Invalid test plan json provided, bailing!", type="fatal")
                self.errors += 1
                self.finish()
                return

        for test in self.test_plan:
            if self.validate_test(test):
                test_name = test.get("test_name")
                fq_name = test.get("module").split(".")
                if len(fq_name) == 3:
                    module_name = ".".join([fq_name[0], fq_name[1]])
                else:
                    module_name = fq_name[0]
                module = self.modules.available_modules.get(module_name)
                self.logger.log(f'Running test: {test_name}', "section")
                if module:
                    if module.run(fq_name[-1], test.get("parameters")):
                        self.logger.log(f"Test {test_name} completed successfully.", type="result")
                        self.tests_passed += 1
                    else:
                        self.logger.log(f"Test {test_name} has failed.", type="failure")
                        self.tests_failed += 1
                else:
                    self.logger.log(f'Module for {test_name} not found, skipped!', type="failure")
                    self.errors += 1
                # Store test count
                self.total_tests += 1
                     
        self.finish()
    
    def validate_test(self, test):
        name = test.get("test_name", None)
        module = test.get("module", None)
        if name and module:
            self.logger.log(f'Test {name} in the test plan has been deemed valid!', type="debug")
            return True
        self.logger.log(f'Test {name} in the test plan has been deemed invalid and has been skipped!', type="summary")
        self.errors += 1
        return False
    
    def finish(self):
        self.logger.log("Test Execution Summary:", type="summarySpaced")
        self.logger.log(f"Total parsed tests: {self.total_tests}", type="result")
        self.logger.log(f"Passed: {self.tests_passed}", type="result")
        if self.tests_failed > 0:
            self.logger.log(f"Failed: {self.tests_failed}", type="failure")
        if self.errors > 0:
            self.logger.log(f"Errors: {self.errors}", type="failure")