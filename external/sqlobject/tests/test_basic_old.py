from sqlobject import *
from sqlobject.tests.dbtest import *

deprecated_module()

class OldTestSO1(SQLObject):

    name = StringCol(length=50, dbName='name_col')
    _cacheValues = False
    _columns = [
        StringCol('passwd', length=10),
        ]

    def _set_passwd(self, passwd):
        self._SO_set_passwd(passwd.encode('rot13'))

def setupGetters(cls):
    setupClass(cls)
    inserts(cls, [('bob', 'god'), ('sally', 'sordid'),
                  ('dave', 'dremel'), ('fred', 'forgo')],
            'name passwd')

def test_case1():
    setupGetters(OldTestSO1)
    bob = OldTestSO1.selectBy(name='bob')[0]
    assert bob.name == 'bob'
    assert bob.passwd == 'god'.encode('rot13')

def test_newline():
    setupGetters(OldTestSO1)
    bob = OldTestSO1.selectBy(name='bob')[0]
    testString = 'hey\nyou\\can\'t you see me?\t'
    bob.name = testString
    bob.expire()
    assert bob.name == testString

def test_count():
    setupGetters(OldTestSO1)
    assert OldTestSO1.selectBy(name='bob').count() == 1
    assert OldTestSO1.select(OldTestSO1.q.name == 'bob').count() == 1
    assert OldTestSO1.select().count() == len(list(OldTestSO1.select()))

def test_getset():
    setupGetters(OldTestSO1)
    bob = OldTestSO1.selectBy(name='bob')[0]
    assert bob.name == 'bob'
    bob.name = 'joe'
    assert bob.name == 'joe'

teardown_module()
