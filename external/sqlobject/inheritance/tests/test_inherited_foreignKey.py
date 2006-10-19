from sqlobject import *
from sqlobject.tests.dbtest import *
from sqlobject.inheritance import InheritableSQLObject


class Note(SQLObject):
    text = StringCol()

class PersonWithNotes(InheritableSQLObject):
    firstName = StringCol()
    lastName = StringCol()
    note = ForeignKey("Note", default=None)

class Paper(SQLObject):
    content = StringCol()

class EmployeeWithNotes(PersonWithNotes):
    _inheritable = False
    paper = ForeignKey("Paper", default=None)

def setup():
    setupClass(Note)
    setupClass(PersonWithNotes)
    setupClass(Paper)
    setupClass(EmployeeWithNotes)

    note = Note(text="person")
    PersonWithNotes(firstName='Oneof', lastName='Authors', note=note)
    note = Note(text="employee")
    EmployeeWithNotes(firstName='Project', lastName='Leader', note=note)

    paper = Paper(content="secret")
    EmployeeWithNotes(firstName='Senior', lastName='Clerk', paper=paper)
    PersonWithNotes(firstName='Some', lastName='Person')

def test_inheritance():
    setup()
    person = PersonWithNotes.get(1)
    assert isinstance(person, PersonWithNotes) and not isinstance(person, EmployeeWithNotes)
    assert person.note.text == "person"

    employee = EmployeeWithNotes.get(2)
    assert isinstance(employee, EmployeeWithNotes)
    assert employee.note.text == "employee"

    persons = PersonWithNotes.select(PersonWithNotes.q.noteID <> None)
    assert persons.count() == 2

    persons = PersonWithNotes.selectBy(noteID=person.note.id)
    assert persons.count() == 1

    persons = EmployeeWithNotes.select(PersonWithNotes.q.noteID <> None)
    assert persons.count() == 1

    persons = PersonWithNotes.selectBy(noteID=person.note.id)
    assert persons.count() == 1

    persons = PersonWithNotes.selectBy(note=person.note)
    assert persons.count() == 1

    persons = PersonWithNotes.selectBy(note=None)
    assert persons.count() == 2

    persons = EmployeeWithNotes.selectBy(paper=None)
    assert persons.count() == 1

    persons = EmployeeWithNotes.selectBy(note=employee.note,
                                         paper=employee.paper)
    assert persons.count() == 1

    persons = EmployeeWithNotes.selectBy()
    assert persons.count() == 2
