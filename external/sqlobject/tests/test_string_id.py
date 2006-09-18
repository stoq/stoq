from sqlobject import *
from sqlobject.tests.dbtest import *

class TestStringID(SQLObject):
    class sqlmeta(sqlmeta):
        idType = str
        idName = 'test_id_here'
    name = StringCol(length=100)

def test_string_id():
    conn = getConnection()
    TestStringID.setConnection(conn)
    TestStringID.dropTable(ifExists=True)
    assert not conn.tableExists(TestStringID.sqlmeta.table)
    TestStringID.createTable()
    TestStringID(id="TestStringID", name="TestStringID name")
    assert len(list(TestStringID.selectBy(id='TestStringID'))) == 1
