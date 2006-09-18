from sqlobject import *
from sqlobject.tests.dbtest import *

class PersonIndexGet(SQLObject):
    firstName = StringCol()
    lastName = StringCol()
    age = IntCol(alternateID=True)
    nameIndex = DatabaseIndex(firstName, lastName, unique=True)

def test_1():
    setupClass(PersonIndexGet, force=True)

    PersonIndexGet(firstName='Eric', lastName='Idle', age=62)
    PersonIndexGet(firstName='Terry', lastName='Gilliam', age=65)
    PersonIndexGet(firstName='John', lastName='Cleese', age=66)

    PersonIndexGet.get(1)
    PersonIndexGet.nameIndex.get('Terry', 'Gilliam')
    PersonIndexGet.nameIndex.get(firstName='John', lastName='Cleese')

    try:
        print PersonIndexGet.nameIndex.get(firstName='Graham', lastName='Chapman')
    except Exception, e:
        pass
    else:
        raise AssertError

    try:
        print PersonIndexGet.nameIndex.get('Terry', lastName='Gilliam')
    except Exception, e:
        pass
    else:
        raise AssertError

    try:
        print PersonIndexGet.nameIndex.get('Terry', 'Gilliam', 65)
    except Exception, e:
        pass
    else:
        raise AssertError

    try:
        print PersonIndexGet.nameIndex.get('Terry')
    except Exception, e:
        pass
    else:
        raise AssertError
