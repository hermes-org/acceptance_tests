"""Command Line Interface for the IPC-Hermes-9852 interface test manager package."""

import argparse
from hermes_test_manager import hermes_test_api

def run_all() -> None:
    """Run all tests."""
    for test in hermes_test_api.available_tests():
        result = hermes_test_api.run_test(test, _callback_handler)
        print(f'Test {test} result: {result}')

def run_test(test_name: str) -> None:
    """Run a specific test."""
    result = hermes_test_api.run_test(test_name, _callback_handler)
    print(f'Test {test_name} result: {result}')

def _callback_handler(*args, **kwargs):
    """Default callback handler."""
    print(args[1])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("test", help="name of test case")
    cmd_args = parser.parse_args()
    testname = cmd_args.test

    print('from cli - ' + testname)
    if testname == 'all':
        run_all()
    else:
        run_test(testname)
