import os
import sys

# The tests require that the environment is currently set to C, to avoid
# translated strings and use the default date/number/currency formatting
os.environ['LC_ALL'] = 'C'
os.environ['LANG'] = 'C'
os.environ['LANGUAGE'] = 'C'

import nose
from nose.plugins import Plugin


class Stoq(Plugin):
    # This is a little hack to make sure that Stoq's database configuration
    # is properly setup. If we import tests.base before Cover.setup() in the
    # coverage plugin is called the statistics will skip the modules imported
    # by tests.base
    def begin(self):
        import tests.base
        tests.base  # pyflakes


# The --with-stoq parameter must be the last provided option,
# specifically, after the --with-coverage module when coverage is enabled
argv = sys.argv[:] + ['--with-stoq']

nose.main(argv=argv, addplugins=[Stoq()])
