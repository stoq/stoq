from kiwi.environ import Library

__all__ = ["library"]

library = Library("stoqdrivers", root="..")
if library.uninstalled:
    # XXX: Move this to enable_translation()
    try:
        library.add_resources(locale='locale')
    except EnvironmentError:
        pass
    library.add_global_resource("conf", "stoqdrivers/conf")
library.enable_translation()
