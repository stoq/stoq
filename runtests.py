#!/usr/bin/env python

import os
import sys

from stoqlib.test.tests_runner import main


if __name__ == '__main__':
    # FIXME: readline is segfaulting when the tests run inside a xvfb
    # environment. Changing it to gnureadline seems to normalize it
    if os.environ.get('PATCH_READLINE', '0') == '1':
        import gnureadline
        sys.modules['readline'] = gnureadline
    main(sys.argv)
