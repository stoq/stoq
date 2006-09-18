from __future__ import generators # for enumerate
from sqlobject import *
from sqlobject.main import SQLObjectIntegrityError
from sqlobject.tests.dbtest import *
from py.test import raises

try:
    enumerate
except NameError:
    def enumerate(iterable):
        i = 0
        for obj in iterable:
            yield i, obj
            i += 1

class IterTest(SQLObject):
    name = StringCol(dbName='name_col')

names = ('a', 'b', 'c')
def setupIter():
    setupClass(IterTest)
    for n in names:
        IterTest(name=n)

def test_00_normal():
    setupIter()
    count = 0
    for test in IterTest.select():
        count += 1
    assert count == len(names)

def test_00b_lazy():
    setupIter()
    count = 0
    for test in IterTest.select(lazyColumns=True):
        count += 1
    assert count == len(names)

def test_01_turn_to_list():
    count = 0
    for test in list(IterTest.select()):
        count += 1
    assert count == len(names)

def test_02_generator():
    all = IterTest.select()
    count = 0
    for i, test in enumerate(all):
        count += 1
    assert count == len(names)

def test_03_ranged_indexed():
    all = IterTest.select()
    count = 0
    for i in range(all.count()):
        test = all[i]
        count += 1
    assert count == len(names)

def test_04_indexed_ended_by_exception():
    if not supports('limitSelect'):
        return
    all = IterTest.select()
    count = 0
    try:
        while 1:
            test = all[count]
            count = count+1
            # Stop the test if it's gone on too long
            if count > len(names):
                break
    except IndexError:
        pass
    assert count == len(names)

def test_select_getOne():
    setupClass(IterTest)
    a = IterTest(name='a')
    b = IterTest(name='b')
    assert IterTest.selectBy(name='a').getOne() == a
    assert IterTest.select(IterTest.q.name=='b').getOne() == b
    assert IterTest.selectBy(name='c').getOne(None) is None
    raises(SQLObjectNotFound, 'IterTest.selectBy(name="c").getOne()')
    b2 = IterTest(name='b')
    raises(SQLObjectIntegrityError, 'IterTest.selectBy(name="b").getOne()')
    raises(SQLObjectIntegrityError, 'IterTest.selectBy(name="b").getOne(None)')

def test_selectBy():
    setupClass(IterTest)
    a = IterTest(name='a')
    b = IterTest(name='b')
    assert IterTest.selectBy().count() == 2

def test_selectBy_kwargs():
    setupClass(IterTest)
    try:
        b = IterTest(nonexistant='b')
    except TypeError:
        return
    assert False, "IterTest(nonexistant='b') should raise TypeError"

class Counter2(SQLObject):

    n1 = IntCol(notNull=True)
    n2 = IntCol(notNull=True)

class TestSelect:

    def setup_method(self, meth):
        setupClass(Counter2)
        for i in range(10):
            for j in range(10):
                Counter2(n1=i, n2=j)

    def counterEqual(self, counters, value):
        assert [(c.n1, c.n2) for c in counters] == value

    def accumulateEqual(self, func, counters, value):
        assert func([c.n1 for c in counters]) == value

    def test_1(self):
        try:
            sum
        except NameError:
            def sum(sequence):
                s = 0
                for item in sequence:
                    s = s + item
                return s
        self.accumulateEqual(sum,Counter2.select(orderBy='n1'),
                             sum(range(10)) * 10)

    def test_2(self):
        self.accumulateEqual(len,Counter2.select('all'), 100)

def test_sqlbuilder_LIKE():
    setupClass(IterTest)
    IterTest(name='sqlobject')
    IterTest(name='sqlbuilder')
    assert IterTest.select(LIKE(IterTest.q.name, "sql%")).count() == 2
    assert IterTest.select(LIKE(IterTest.q.name, "sqlb%")).count() == 1
    assert IterTest.select(LIKE(IterTest.q.name, "sqlb%")).count() == 1
    assert IterTest.select(LIKE(IterTest.q.name, "sqlx%")).count() == 0

def test_sqlbuilder_RLIKE():
    setupClass(IterTest)

    if IterTest._connection.dbName == "sqlite":
        from sqlobject.sqlite.sqliteconnection import using_sqlite2
        if not using_sqlite2:
            return

        # Implement regexp() function for SQLite; only works with PySQLite2
        import re
        def regexp(regexp, test):
            return bool(re.search(regexp, test))

        _get_connection = IterTest._connection.getConnection
        def new_get_connection(*args, **kw):
            _connection = _get_connection(*args, **kw)
            _connection.create_function("regexp", 2, regexp)
            return _connection
        IterTest._connection.getConnection = new_get_connection

    IterTest(name='sqlobject')
    IterTest(name='sqlbuilder')
    assert IterTest.select(RLIKE(IterTest.q.name, "^sql.*$")).count() == 2
    assert IterTest.select(RLIKE(IterTest.q.name, "^sqlb.*$")).count() == 1
    assert IterTest.select(RLIKE(IterTest.q.name, "^sqlb.*$")).count() == 1
    assert IterTest.select(RLIKE(IterTest.q.name, "^sqlx.*$")).count() == 0
