# helper function
def remove_suffix(line: str, suffix: str) -> str:
    if line.endswith(suffix):
        return line[:-len(suffix):]
    else:
        return line
