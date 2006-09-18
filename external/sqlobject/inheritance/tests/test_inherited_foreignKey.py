from sqlobject import *
from sqlobject.tests.dbtest import *
from sqlobject.inheritance import InheritableSQLObject


class Note(SQLObject):
    text = StringCol()

class PersonWithNotes(InheritableSQLObject):
    firstName = StringCol()
    lastName = StringCol()
    note = ForeignKey("Note", default=None)

class EmployeeWithNotes(PersonWithNotes):
    _inheritable = False

def setup():
    setupClass(Note)
    setupClass(PersonWithNotes)
    setupClass(EmployeeWithNotes)

    note = Note(text="person")
    PersonWithNotes(firstName='Oneof', lastName='Authors', note=note)
    note = Note(text="employee")
    EmployeeWithNotes(firstName='Project', lastName='Leader', note=note)


def test_inheritance():
    setup()

    person = PersonWithNotes.get(1)
    assert isinstance(person, PersonWithNotes) and not isinstance(person, EmployeeWithNotes)
    assert person.note.text == "person"

    employee = EmployeeWithNotes.get(2)
    assert isinstance(employee, EmployeeWithNotes)
    assert employee.note.text == "employee"
