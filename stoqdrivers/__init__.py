__version__ = (0, 5, 0)

from kiwi.environ import Library

__all__ = ["library"]

library = Library("stoqdrivers", root="..")
if library.uninstalled:
    library.add_global_resource("conf", "stoqdrivers/conf")
library.enable_translation()
