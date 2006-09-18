from sqlobject.dbconnection import registerConnection

def builder():
    import firebirdconnection
    return firebirdconnection.FirebirdConnection

def isSupported():
    try:
        import kinterbasdb
    except ImportError:
        return False
    return True

registerConnection(['firebird', 'interbase'], builder, isSupported)
