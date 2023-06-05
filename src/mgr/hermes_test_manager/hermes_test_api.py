"""API for IPC-Hermes-9852 interface test manager."""
import os
import sys
import logging
import hashlib
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
import test_cases.test_downstream_ifc_interactive
import test_cases.test_upstream_ifc
import test_cases.test_upstream_ifc_interactive

log = logging.getLogger('hermes_test_api')


class TestResult(Enum):
    """Test result enumeration."""
    PASS = "Pass"
    FAIL = "Fail"


class TestInfo():
    """Test information class.
       The tag is a short identifier for the test case but
       its value is not guaranteed to be unique.
    """
    def __init__(self, name: str, module: str, description: str):
        self.name = name
        self.module = module
        self.description = description
        self.tag = "H" + hashlib.md5(bytearray(name, 'utf-8')).hexdigest()[:4]

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
            log.info("Start %s...", testcase)
            func()
        except Exception as exc:
            print(f"FAILED with error: {str(exc)}")
            log.error("Failed: %s, %s", testcase, exc)
            return False
        else:
            log.info("Passed: %s", testcase)
            return True

    print(f'Called unknown test case: {testcase}')
    log.error("Called unknown test case: %s", testcase)
    return False

def setup_default_logging(filename: str, level=logging.INFO, extra_loggers: list=None) -> None:
    """Optional setup of logging to file."""
    formatter = logging.Formatter('%(asctime)-19s.%(msecs)-3d [%(name)-15s] %(levelname)s: %(message)s',
                                  '%Y-%m-%dT%H:%M:%S')
    file_handler = logging.FileHandler(filename, mode='w', encoding='utf-8')
    file_handler.setFormatter(formatter)
    loggers = ['hermes_test_api','ipc_hermes','test_cases']
    loggers.extend(extra_loggers or [])
    for log_name in loggers:
        logger = logging.getLogger(log_name)
        logger.setLevel(level)
        logger.addHandler(file_handler)

if __name__ == '__main__':
    # Print a list of available tests and some usage hints, any CLI should be in another file
    print('Available tests:')
    for test_name in get_test_dictionary():
        print(test_name)
