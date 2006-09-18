from main import *
from col import *
from sqlbuilder import AND, OR, NOT, IN, LIKE, RLIKE, DESC, CONTAINSSTRING, const, func
from styles import *
from joins import *
from index import *
from dbconnection import connectionForURI

## Each of these imports allows the driver to install itself
## Then we set up some backward compatibility

def _warn(msg):
    import warnings
    warnings.warn(msg, DeprecationWarning, stacklevel=2)

import firebird as _firebird
def FirebirdConnection(*args, **kw):
    _warn('FirebirdConnection is deprecated; use connectionForURI("firebird://...") or "from sqlobject.firebird import builder; FirebirdConnection = builder()"')
    return _firebird.builder()(*args, **kw)

import mysql as _mysql
def MySQLConnection(*args, **kw):
    _warn('MySQLConnection is deprecated; use connectionForURI("mysql://...") or "from sqlobject.mysql import builder; MySQLConnection = builder()"')
    return _mysql.builder()(*args, **kw)

import postgres as _postgres
def PostgresConnection(*args, **kw):
    _warn('PostgresConnection is deprecated; use connectionForURI("postgres://...") or "from sqlobject.postgres import builder; PostgresConnection = builder()"')
    return _postgres.builder()(*args, **kw)

import sqlite as _sqlite
def SQLiteConnection(*args, **kw):
    _warn('SQLiteConnection is deprecated; use connectionForURI("sqlite://...") or "from sqlobject.sqlite import builder; SQLiteConnection = builder()"')
    return _sqlite.builder()(*args, **kw)

import sybase as _sybase
def SybaseConnection(*args, **kw):
    _warn('SybaseConnection is deprecated; use connectionForURI("sybase://...") or "from sqlobject.sybase import builder; SybaseConnection = builder()"')
    return _sybase.builder()(*args, **kw)

import maxdb as _maxdb
def MaxdbConnection(*args, **kw):
    _warn('MaxdbConnection is deprecated; use connectionForURI("maxdb://...") or "from sqlobject.maxdb import builder; MaxdbConnection = builder()"')
    return _maxdb.builder()(*args, **kw)

import mssql as _mssql
def MSSQLConnection(*args, **kw):
        _warn('MssqlConnection is deprecated; use connectionForURI("mssql://...") or "from sqlobject.mssql import builder; MSSQLConnection = builder()"')
        return _mssql.builder()(*args, **kw)
