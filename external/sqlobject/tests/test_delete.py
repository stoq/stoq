from sqlobject import *
from sqlobject.tests.dbtest import *
from test_basic import TestSO1, setupGetters

########################################
## Delete during select
########################################

def testSelect():
    setupGetters(TestSO1)
    for obj in TestSO1.select('all'):
        obj.destroySelf()
    assert list(TestSO1.select('all')) == []

########################################
## Delete without caching
########################################

class NoCache(SQLObject):
    name = StringCol()

def testDestroySelf():
    setupClass(NoCache)
    old = NoCache._connection.cache
    NoCache._connection.cache = cache.CacheSet(cache=False)
    value = NoCache(name='test')
    value.destroySelf()
    NoCache._connection.cache = old
