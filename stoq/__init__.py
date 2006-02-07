from kiwi.environ import Library

__program_name__    = "Stoq"
__website__         = 'http://www.stoq.com.br'
__version__         = "0.6.0"
__release_date__    = (2006, 1, 27)

__all__ = ['library']

library = Library('stoq', root='..')
if library.uninstalled:
    library.add_global_resources(pixmaps='pixmaps')
