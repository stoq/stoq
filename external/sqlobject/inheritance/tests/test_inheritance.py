from sqlobject import *
from sqlobject.tests.dbtest import *
from sqlobject.inheritance import InheritableSQLObject

########################################
## Inheritance
########################################


class InheritablePerson(InheritableSQLObject):
    firstName = StringCol()
    lastName = StringCol(alternateID=True, length=255)

class Employee(InheritablePerson):
    _inheritable = False
    position = StringCol()

def setup():
    setupClass(InheritablePerson)
    setupClass(Employee)

    Employee(firstName='Project', lastName='Leader', position='Project leader')
    InheritablePerson(firstName='Oneof', lastName='Authors')


def test_inheritance():
    setup()

    persons = InheritablePerson.select() # all
    for person in persons:
        assert isinstance(person, InheritablePerson)
        if isinstance(person, Employee):
            assert not hasattr(person, "childName")
        else:
            assert hasattr(person, "childName")
            assert not person.childName


def test_inheritance_select():
    setup()

    persons = InheritablePerson.select(InheritablePerson.q.firstName <> None)
    assert persons.count() == 2

    persons = InheritablePerson.select(InheritablePerson.q.firstName == "phd")
    assert persons.count() == 0

    employees = Employee.select(Employee.q.firstName <> None)
    assert employees.count() == 1

    employees = Employee.select(Employee.q.firstName == "phd")
    assert employees.count() == 0

    employees = Employee.select(Employee.q.position <> None)
    assert employees.count() == 1

    persons = InheritablePerson.selectBy(firstName="Project")
    assert persons.count() == 1
    assert isinstance(persons[0], Employee)

    persons = Employee.selectBy(firstName="Project")
    assert persons.count() == 1

    try:
        person = InheritablePerson.byLastName("Oneof")
    except:
        pass
    else:
        raise RuntimeError, "unknown person %s" % person

    person = InheritablePerson.byLastName("Leader")
    assert person.firstName == "Project"

    person = Employee.byLastName("Leader")
    assert person.firstName == "Project"

def test_addDelColumn():
    setup()

    assert hasattr(InheritablePerson, "firstName")
    assert hasattr(Employee, "firstName")
    assert hasattr(InheritablePerson.q, "firstName")
    assert hasattr(Employee.q, "firstName")

    Employee.sqlmeta.addColumn(IntCol('runtime', default=None))

    assert not hasattr(InheritablePerson, 'runtime')
    assert hasattr(Employee, 'runtime')
    assert not hasattr(InheritablePerson.q, 'runtime')
    assert hasattr(Employee.q, 'runtime')

    InheritablePerson.sqlmeta.addColumn(IntCol('runtime2', default=None))

    assert hasattr(InheritablePerson, 'runtime2')
    assert hasattr(Employee, 'runtime2')
    assert hasattr(InheritablePerson.q, 'runtime2')
    assert hasattr(Employee.q, 'runtime2')

    Employee.sqlmeta.delColumn('runtime')

    assert not hasattr(InheritablePerson, 'runtime')
    assert not hasattr(Employee, 'runtime')
    assert not hasattr(InheritablePerson.q, 'runtime')
    assert not hasattr(Employee.q, 'runtime')

    InheritablePerson.sqlmeta.delColumn('runtime2')

    assert not hasattr(InheritablePerson, 'runtime2')
    assert not hasattr(Employee, 'runtime2')
    assert not hasattr(InheritablePerson.q, 'runtime2')
    assert not hasattr(Employee.q, 'runtime2')
