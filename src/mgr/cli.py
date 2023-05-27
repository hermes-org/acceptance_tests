"""Command Line Interface for the IPC-Hermes-9852 interface test manager package."""

import argparse
from hermes_test_manager import hermes_test_api

LOG_FILE = "hitmanager.log"

def show_list() -> None:
    """Show all available tests."""
    print('Available tests:')
    for test_name in hermes_test_api.available_tests():
        print(test_name)

def run_all() -> None:
    """Run all tests."""
    for test in hermes_test_api.available_tests():
        result = hermes_test_api.run_test(test, _callback_handler,  verbose)
        print(f'Test {test} result: {result}')
        if result is False:
            break

def run_test(test_name: str) -> None:
    """Run a specific test."""
    result = hermes_test_api.run_test(test_name, _callback_handler, verbose)
    print(f'Test {test_name} result: {result}')

def _callback_handler(*args, **kwargs):
    """Default callback handler."""
    print(args[1])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list", action='store_true', help="list all available test cases")
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="increase output verbosity, recommended if Hermes Testdriver is used")
    parser.add_argument("test", nargs='?', help="name of test case")
    cmd_args = parser.parse_args()
    testname = cmd_args.test
    verbose = cmd_args.verbose

    hermes_test_api.setup_default_logging(LOG_FILE)
    if testname is None:
        show_list()
    elif testname == 'all':
        run_all()
    else:
        run_test(testname)
