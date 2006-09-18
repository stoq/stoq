from sqlobject import *
from sqlobject.tests.dbtest import *
from formencode import Invalid

########################################
## Enum test
########################################

class Enum1(SQLObject):

    l = EnumCol(enumValues=['a', 'bcd', 'e'])

def testBad():
    setupClass(Enum1)
    for l in ['a', 'bcd', 'a', 'e']:
        Enum1(l=l)
    raises(
        (Enum1._connection.module.IntegrityError,
         Enum1._connection.module.ProgrammingError,
         Invalid),
        Enum1, l='b')

class EnumWithNone(SQLObject):

    l = EnumCol(enumValues=['a', 'bcd', 'e', None])

def testNone():
    setupClass(EnumWithNone)
    for l in [None, 'a', 'bcd', 'a', 'e', None]:
        EnumWithNone(l=l)
    
