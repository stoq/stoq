from sqlobject import *
from sqlobject.tests.dbtest import *

deprecated_module()

########################################
## String ID test
########################################

class OldSOStringID(SQLObject):

    _table = 'so_string_id'
    _idType = str
    val = StringCol(alternateID=True)

    mysqlCreate = """
    CREATE TABLE IF NOT EXISTS so_string_id (
      id VARCHAR(50) PRIMARY KEY,
      val TEXT
    )
    """

    postgresCreate = """
    CREATE TABLE so_string_id (
      id VARCHAR(50) PRIMARY KEY,
      val TEXT
    )
    """

    sybaseCreate = """
    CREATE TABLE so_string_id (
      id VARCHAR(50) UNIQUE,
      val VARCHAR(50) NULL
    )
    """

    mssqlCreate = """
    CREATE TABLE so_string_id (
      id VARCHAR(50) primary key,
      val VARCHAR(50) NULL
    )
    """

    firebirdCreate = """
    CREATE TABLE so_string_id (
      id VARCHAR(50) NOT NULL PRIMARY KEY,
      val BLOB SUB_TYPE TEXT
    )
    """

    sqliteCreate = postgresCreate

    mysqlDrop = """
    DROP TABLE IF EXISTS so_string_id
    """

    postgresDrop = """
    DROP TABLE so_string_id
    """

    sqliteDrop = postgresDrop
    firebirdDrop = postgresDrop
    mssqlDrop = postgresDrop


def test_stringID():
    setupClass(OldSOStringID)
    t = OldSOStringID(id='hey', val='whatever')
    t2 = OldSOStringID.byVal('whatever')
    assert t == t2
    t3 = OldSOStringID(id='you', val='nowhere')
    t4 = OldSOStringID.get('you')
    assert t3 == t4
