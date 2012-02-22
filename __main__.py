# bootstrap script used to make an egg executable
# bdist_egg picks it up automatically

import sys

from stoq.main import main

sys.exit(main(sys.argv))
