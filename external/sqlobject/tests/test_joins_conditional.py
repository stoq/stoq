from sqlobject import *
from sqlobject.sqlbuilder import *
from sqlobject.tests.dbtest import *

########################################
## Condiotional joins
########################################

class TestJoin1(SQLObject):
    col1 = StringCol()

class TestJoin2(SQLObject):
    col2 = StringCol()

class TestJoin3(SQLObject):
    col3 = StringCol()

def setup():
    setupClass(TestJoin1)
    setupClass(TestJoin2)

def test_1syntax():
    setup()
    join = JOIN("table1", "table2")
    assert str(join) == "table1 JOIN table2"
    join = LEFTJOIN("table1", "table2")
    assert str(join) == "table1 LEFT JOIN table2"
    join = LEFTJOINOn("table1", "table2", "tabl1.col1 = table2.col2")
    assert getConnection().sqlrepr(join) == "table1 LEFT JOIN table2 ON tabl1.col1 = table2.col2"

def test_2select_syntax():
    setup()
    select = TestJoin1.select(
        join=LEFTJOINConditional(TestJoin1, TestJoin2,
            on_condition=(TestJoin1.q.col1 == TestJoin2.q.col2))
    )
    assert str(select) == \
        "SELECT test_join1.id, test_join1.col1 FROM  test_join1 LEFT JOIN test_join2 ON (test_join1.col1 = test_join2.col2) WHERE 1 = 1"

def test_3perform_join():
    setup()
    TestJoin1(col1="test1")
    TestJoin1(col1="test2")
    TestJoin1(col1="test3")
    TestJoin2(col2="test1")
    TestJoin2(col2="test2")

    select = TestJoin1.select(
        join=LEFTJOINOn(TestJoin1, TestJoin2, TestJoin1.q.col1 == TestJoin2.q.col2)
    )
    assert select.count() == 3

def test_4join_3tables_syntax():
    setup()
    setupClass(TestJoin3)

    select = TestJoin1.select(
        join=LEFTJOIN(TestJoin2, TestJoin3)
    )
    assert str(select) == \
        "SELECT test_join1.id, test_join1.col1 FROM test_join1, test_join2 LEFT JOIN test_join3 WHERE 1 = 1"

def test_5join_3tables_syntax2():
    setup()
    setupClass(TestJoin3)

    select = TestJoin1.select(
        join=(LEFTJOIN(None, TestJoin2), LEFTJOIN(None, TestJoin3))
    )
    assert str(select) == \
        "SELECT test_join1.id, test_join1.col1 FROM test_join1  LEFT JOIN test_join2  LEFT JOIN test_join3 WHERE 1 = 1"
