"""API for IPC-Hermes-9852 interface test manager."""
import os
import sys
import logging
from enum import Enum

# ugly hack to allow GUI app to use hermes_test_manager package without installing it
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# pylint: disable=wrong-import-position
from test_cases import get_test_dictionary
from test_cases import EnvironmentManager

# imports are needed to locate available tests but not used directly by API
# pylint: disable=unused-import
import test_cases.test_cases_dummy
import test_cases.test_downstream_ifc
import test_cases.test_downstream_ifc_states
import test_cases.test_downstream_ifc_interactive
import test_cases.test_upstream_ifc

log = logging.getLogger('hermes_test_api')


class TestResult(Enum):
    """Test result enumeration."""
    PASS = "Pass"
    FAIL = "Fail"


class TestInfo():
    """Test information class."""
    def __init__(self, name: str, module: str, description: str):
        self.name = name
        self.module = module
        self.description = description

    def __str__(self):
        return f"{self.module}.{self.name}"


def available_tests() -> dict:
    """Return a dictionary with TestInfo objects about available tests."""
    test_infos = {}
    for name, test_info in get_test_dictionary().items():
        test_infos[name] = TestInfo(name, test_info[1], test_info[2])
    return test_infos

def run_test(testcase: str, callback=None, verbose=False) -> bool:
    """Run a single test case.

    Args:
        testcase: Name of the test case to run.
        callback: Callback function to be called when the test case is finished.

    Return: True if the test case was found and executed, False otherwise.
    """
    env = EnvironmentManager()
    env.use_handshake_callback = verbose
    env.use_wrapper_callback = verbose
    if callback is not None:
        # TODO verify callback when final format decided
        env.register_callback(callback)

    test_info = get_test_dictionary().get(testcase)
    func = test_info[0]
    if func is not None:
        try:
            log.debug("Executing '%s'...", testcase)
            func()
        except Exception as exc:
            print(f"FAILED with error: {str(exc)}")
            log.error("Finished '%s' with result: %s, %s", testcase, TestResult.FAIL.value, exc)
            return False
        else:
            log.info("Finished '%s' with result: %s", testcase, TestResult.PASS.value)
            return True

    print(f'Called unknown test case {testcase}')
    log.error("Finished '%s' with result: %s", testcase, TestResult.FAIL.value)
    return False


if __name__ == '__main__':
    # Print a list of available tests and some usage hints, any CLI should be in another file
    print('Available tests:')
    for test_name in get_test_dictionary():
        print(test_name)
