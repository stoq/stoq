import os
from Kiwi2 import gladepath, set_gladepath
import stoqlib

path = [os.path.join(stoqlib.__path__[0], "interface", "glade")]

# If it doesn't already exists in the gladepath, add it
if path not in gladepath:
    set_gladepath(gladepath + path)

