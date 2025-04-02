from enum import Enum

class TaskType(str, Enum):
    TRAIN = 'train'
    CODE = 'code'
    UNKNOWN = 'unknown'


