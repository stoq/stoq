#!/usr/bin/env python
import os
import sys

from twisted.trial.runner import TestLoader, TrialRunner
from twisted.trial.reporter import TextReporter

# Some tests depends on the language being set to english
os.environ['LC_ALL'] = 'C'
os.environ['LANG'] = 'C'

names = []
for name in sys.argv[1:]:
    if name[-1] == '/':
        name = name[:-1]
    names.append(name)

loader = TestLoader()
tests = loader.loadByNames(names, recurse=True)
runner = TrialRunner(TextReporter)
runner.run(tests)
