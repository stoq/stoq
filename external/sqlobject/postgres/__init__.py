from sqlobject.dbconnection import registerConnection

def builder():
    import pgconnection
    return pgconnection.PostgresConnection

def isSupported():
    try:
        import psycopg2
    except ImportError:
        try:
            import psycopg
        except ImportError:
            return False
    return True

registerConnection(['postgres', 'postgresql', 'psycopg'],
                   builder, isSupported)
