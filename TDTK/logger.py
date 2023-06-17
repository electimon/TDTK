# Logger for TDTK
from datetime import datetime
from time import time

class LogColors:
    INFO = "\033[96m"
    SUCCESS = "\033[92m"
    ERROR = "\033[91m"
    DEBUG = "\033[95m"
    END = "\033[0m"

class LogTypes:
    hyphenSpacers = "\n" + "-" * 50
    hyphenSpacersSpaced = hyphenSpacers + "\n"
    plainSpaced = {"prefix": "", "suffix": "\n", "indent": 0, "color": LogColors.INFO}
    plain = {"prefix": "", "indent": 0, "color": LogColors.INFO}
    section = {"prefix": hyphenSpacersSpaced, "suffix": hyphenSpacers, "indent": 0, "color": LogColors.INFO}
    subsection = {"prefix": "\n", "indent": 1, "color": LogColors.INFO}
    result = {"prefix": "  - ", "indent": 1, "color": LogColors.SUCCESS}
    failure = {"prefix": "  - ", "indent": 1, "color": LogColors.ERROR}
    fatal = {"prefix": "\n  - ", "indent": 2, "color": LogColors.ERROR}
    plainFailure = {"prefix": "", "indent": 0, "color": LogColors.ERROR}
    summary = {"prefix": "", "indent": 0, "color": LogColors.INFO}
    summarySpaced = {"prefix": "\n", "indent": 0, "color": LogColors.INFO}
    debug = {"prefix": "DEBUG: ", "indent": 0, "color": LogColors.DEBUG}
    ratelimited = {"prefix": "", "indent": 0, "color": LogColors.INFO}
    
    def get(self, type, fallback):
        return getattr(self, type, fallback)

class Logger:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
        return cls._instance
    
    def __init__(self, caller) -> None:
        self.ratelimit_threshold = 2
        self.ratelimit_last_log_time = 0
        self.types = LogTypes()
        self.caller = caller
        if hasattr(caller, "debug"):
            self.debug = caller.debug
        else:
            self.debug = False
    
    def log(self, message: str, type: str = ""):
        if not self.debug == True and type == "debug":
            return
        log_type = self.types.get(type, {"prefix": "", "indent": 0, "color": LogColors.INFO, "found": False})
        if not log_type.get("found", True):
            self.log(f'Log Type for message: "{message}" was not defined.', type="failure")
        if type == "ratelimited":
            current_time = time()
            if current_time - self.ratelimit_last_log_time < 1 / self.ratelimit_threshold:
                return
            self.ratelimit_last_log_time = current_time

        indent = "  " * log_type["indent"]
        color = log_type["color"]
        prefix = log_type.get("prefix", "")
        suffix = log_type.get("suffix", "")
        print(f"{color}{indent}{prefix}{message}{suffix}{LogColors.END}")

    def log_summary(self, total_tests: int, passed: int, failed: int, errors: int):
        self.log("Test Execution Summary:", type="summarySpaced")
        self.log(f"Total parsed tests: {total_tests}", type="result")
        self.log(f"Passed: {passed}", type="result")
        if failed > 0:
            self.log(f"Failed: {failed}", type="failure")
        if errors > 0:
            self.log(f"Errors: {errors}", type="failure")

    def start(self):
        self.log("Terra Debug Tool Kit (TDTK) - Test Execution Report", type="plainSpaced")
        if hasattr(self.caller, "test_plan"):
            self.log(f'Test Plan: {self.caller.test_plan}', type="plain")
        if hasattr(self.caller, "device"):
            self.log(f'Device: {self.caller.device.serial}', type="plain")
        self.log(f'Date: {datetime.today().strftime("%b %d, %Y")}', type="plain")
