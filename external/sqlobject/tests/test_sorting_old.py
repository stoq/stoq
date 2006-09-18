from sqlobject import *
from sqlobject.tests.dbtest import *

deprecated_module()

class OldNames(SQLObject):

    _table = 'names_table'

    firstName = StringCol(length=30)
    lastName = StringCol(length=30)

    _defaultOrder = ['lastName', 'firstName']

def setupNames():
    setupClass(OldNames)
    inserts(OldNames, [('aj', 'baker'), ('joe', 'robbins'),
                    ('tim', 'jackson'), ('joe', 'baker'),
                    ('zoe', 'robbins')],
            schema='firstName lastName')

def nameList(names):
    result = []
    for name in names:
        result.append('%s %s' % (name.firstName, name.lastName))
    return result

def firstList(names):
    return [n.firstName for n in names]

def test_defaultOrder():
    setupNames()
    assert nameList(OldNames.select()) == \
           ['aj baker', 'joe baker',
            'tim jackson', 'joe robbins',
            'zoe robbins']
