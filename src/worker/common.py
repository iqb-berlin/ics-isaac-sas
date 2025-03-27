import sys

def print_in_worker(*args):
    print(args)
    sys.stdout.flush()

