import argparse
from TDTK.test_runner import TestRunner

def main():
    parser = argparse.ArgumentParser(description="TerraDebugToolKit (TDTK) - CLI Tool")

    # Test plan argument
    parser.add_argument("test_plan", help="Path to the test plan JSON file")

    # Device ID argument
    parser.add_argument("-i", "--id", dest="device_id", default="",
                        help="Device ID of the Android phone")

    # Debug argument
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")

    args = parser.parse_args()

    # Setup and start the test runner
    runner = TestRunner(args)
    if runner:
        runner.start()

if __name__ == "__main__":
    main()
