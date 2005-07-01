import os

from kiwi.environ import get_gladepath, set_gladepath

import stoqlib

path = [os.path.join(stoqlib.__path__[0], "gui", "glade")]

# If it doesn't already exists in the gladepath, add it
gladepath = get_gladepath()
if path not in gladepath:
    set_gladepath(gladepath + path)

