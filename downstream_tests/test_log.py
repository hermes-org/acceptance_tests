from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import json
import sys
import os

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'

class Level(Enum):
    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"
    FATAL_ERROR = "FatalError"

class TestResult(Enum):
    PASS = "Pass"
    FAIL = "Fail"

def time_now():
    return datetime.now().strftime(DATETIME_FORMAT)

@dataclass
class LogEntry:
    time : str = field(default_factory=time_now)
    level : str = Level.INFO.value

@dataclass
class StartEntry(LogEntry):
    start : None = None
    test_case : str = None

@dataclass
class FinishEntry(LogEntry):
    finish : None = None
    test_case : str = None
    result : str = None

@dataclass
class SentEntry(LogEntry):
    msg : bytes = None

@dataclass
class ReceivedEntry(LogEntry):
    msg : bytes = None

@dataclass
class TransitionEntry(LogEntry):
    src : str = None
    tag : str = None
    tgt : str = None

@dataclass
class TextEntry(LogEntry):
    text : str = None

class TestLog:
    def __init__(self, name):
        self._name = name
        self._start = now = datetime.now()
        try:
            os.mkdir("logs")
        except:
            pass
        self._file_name = "logs/TestLog_" + name + now.strftime('_%Y_%m_%dTH_%M_%S') + ".jsonl"
        self._file = None
    
    def open(self):
        try:
            self._file = open(self._file_name, 'wt')
        except IOError:
            sys.stderr.write(f'Unable to open log file <{self._file_name}')
            raise

        self._log(StartEntry())

    def close(self):
        if (self._file is not None) & (not self._file.closed):
            self._log(FinishEntry())
            self._file.close()

    def log_start(self, test_case):
        self._log(StartEntry(test_case=test_case))

    def log_finish(self, test_case, result):
        self._log(FinishEntry(test_case=test_case, result=result.value))

    def log_sent(self, msg):
        self._log(SentEntry(msg = msg))

    def log_received(self, msg):
        self._log(ReceivedEntry(msg = msg))

    def log_transition(self, src, tag, tgt):
        self._log(TransitionEntry(src = src.value, tag = tag, tgt = tgt.value))

    def log_text(self, text):
        self._log(TextEntry(text = text))

    def _log(self, entry):
        try:
            self._file.write(json.dumps(asdict(entry)))
            self._file.write('\n')
        except Exception:
            sys.stderr.write(f'Failed to append <{entry}> to log file {self._file_name}\n')

def print_and_log(text, test_log):
    print(text)
    test_log.log_text(text)

@contextmanager
def create_log(name):
    log = TestLog(name)
    try:
        log.open()
        yield log
    except:
        raise
    finally:
        log.close()
        