from __future__ import generators

__all__ = ['count', 'enumerate']

# An implementation of itertools' count()
try:
    from itertools import count
except ImportError:
    def count(start=0):
        while 1:
            yield start
            start += 1

try:
    enumerate
except NameError:
    def enumerate(lst):
        i = 0
        for item in lst:
            yield i, item
            i += 1
