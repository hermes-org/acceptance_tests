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

def time_now():
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')

@dataclass
class LogEntry:
    time : str = field(default_factory=time_now)
    level : str = Level.INFO.value

@dataclass
class StartEntry(LogEntry):
    start : None = None

@dataclass
class FinishEntry(LogEntry):
    finish : None = None

@dataclass
class SentEntry(LogEntry):
    msg : bytes = None

@dataclass
class ReceivedEntry(LogEntry):
    msg : bytes = None

@dataclass
class TransitionEntry(LogEntry):
    src : str = None
    msg : str = None
    tgt : str = None

class TestLog:
    def __init__(self, name):
        self._name = name
        self._start = now = datetime.now()
        try:
            os.mkdir("logs");
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

    def log_sent(self, msg):
        self._log(SentEntry(msg = msg))

    def log_received(self, msg):
        self._log(ReceivedEntry(msg = msg))

    def log_transition(self, src, msg, tgt):
        self._log(TransitionEntry(src = src, msg = msg, tgt = tgt))

    def _log(self, entry):
        try:
            self._file.write(json.dumps(asdict(entry)))
            self._file.write('\n')
        except Exception as ex:
            sys.stderr.write(f'Failed to append <{entry}> to log file {self._file_name}\n')

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
        