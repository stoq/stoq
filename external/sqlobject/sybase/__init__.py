from sqlobject.dbconnection import registerConnection

def builder():
    import sybaseconnection
    return sybaseconnection.SybaseConnection

def isSupported(cls):
    try:
        import Sybase
    except ImportError:
        return False
    return True

registerConnection(['sybase'], builder, isSupported)
