import os

os.environ['LC_ALL'] = 'C'
os.environ['LANG'] = 'C'
os.environ['LANGUAGE'] = 'C'

import nose

import tests.base

nose.main()
