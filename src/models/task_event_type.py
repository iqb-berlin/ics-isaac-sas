from enum import Enum


class TaskEventType(str, Enum):
    CREATE = 'create'
    COMMIT = 'commit'
    START = 'start'
    FAIL = 'fail'
    FINISH = 'finish'
    ABORT = 'abort'
