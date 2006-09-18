import os
from sqlobject.dbconnection import DBConnection

########################################
## Test _parseURI
########################################

def test_parse():
    _parseURI = DBConnection._parseURI

    user, password, host, port, path, args = _parseURI("mysql://user:password@host/database")
    assert user == "user"
    assert password == "password"
    assert host == "host"
    assert port is None
    assert path == "/database"
    assert args == {}

    user, password, host, port, path, args = _parseURI("mysql://host/database")
    assert user is None
    assert password is None
    assert host == "host"
    assert port is None
    assert path == "/database"
    assert args == {}

    user, password, host, port, path, args = _parseURI("postgres://user@host/database")
    assert user == "user"
    assert password is None
    assert host == "host"
    assert port is None
    assert path == "/database"
    assert args == {}

    user, password, host, port, path, args = _parseURI("postgres://host:5432/database")
    assert user is None
    assert password is None
    assert host == "host"
    assert port == 5432
    assert path == "/database"
    assert args == {}

    user, password, host, port, path, args = _parseURI("sqlite:///full/path/to/database")
    assert user is None
    assert password is None
    assert host is None
    assert port is None
    assert path == "/full/path/to/database"
    assert args == {}

    user, password, host, port, path, args = _parseURI("sqlite:/:memory:")
    assert user is None
    assert password is None
    assert host is None
    assert port is None
    assert path == "/:memory:"
    assert args == {}

    if os.name == 'nt':
        user, password, host, port, path, args = _parseURI("sqlite:/C|/full/path/to/database")
        assert user is None
        assert password is None
        assert host is None
        assert port is None
        assert path == "C:/full/path/to/database"
        assert args == {}
