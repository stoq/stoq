from sqlobject.dbconnection import registerConnection

def builder():
    import mssqlconnection
    return mssqlconnection.MSSQLConnection

def isSupported(cls):
    try:
        import pymssql
    except ImportError:
        try:
            import adodbapi
        except ImportError:
            return False
    return True

registerConnection(['mssql'], builder, isSupported)
