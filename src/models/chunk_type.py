from enum import Enum


class ChunkType(str, Enum):
    INPUT = 'input'
    OUTPUT = 'output'
