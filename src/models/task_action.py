from enum import Enum


class TaskAction(str, Enum):
    COMMIT = 'commit'
    ABORT = 'abort'
