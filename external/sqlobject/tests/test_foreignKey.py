from sqlobject import *
from sqlobject.tests.dbtest import *

class TestComposerKey(SQLObject):
    name = StringCol()

class TestWorkKey(SQLObject):
    class sqlmeta:
        idName = "work_id"

    composer = ForeignKey('TestComposerKey', cascade=True)
    title = StringCol()

class TestWorkKey2(SQLObject):
    title = StringCol()

def test1():
    setupClass([TestComposerKey, TestWorkKey])

    c = TestComposerKey(name='Mahler, Gustav')
    w1 = TestWorkKey(composer=c, title='Symphony No. 9')
    w2 = TestWorkKey(composer=None, title=None)

    # Select by usual way
    s = TestWorkKey.selectBy(composerID=c.id, title='Symphony No. 9')
    assert s[0]==w1
    # selectBy object.id
    s = TestWorkKey.selectBy(composer=c.id, title='Symphony No. 9')
    assert s[0]==w1
    # selectBy object
    s = TestWorkKey.selectBy(composer=c, title='Symphony No. 9')
    assert s[0]==w1
    # selectBy id
    s = TestWorkKey.selectBy(id=w1.id)
    assert s[0]==w1
    # is None handled correctly?
    s = TestWorkKey.selectBy(composer=None, title=None)
    assert s[0]==w2

def test2():
    setupClass([TestComposerKey, TestWorkKey2], force=True)
    TestWorkKey2.sqlmeta.addColumn(ForeignKey('TestComposerKey'), changeSchema=True)
