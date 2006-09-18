from sqlobject import *
from sqlobject.tests.dbtest import *

class PersonWithAlbum(SQLObject):
    name = StringCol()
    # albumNone returns the album or none
    albumNone = SingleJoin('PhotoAlbum', joinColumn='person_id')
    # albumInstance returns the album or an default album instance
    albumInstance = SingleJoin('PhotoAlbum', makeDefault=True, joinColumn='person_id')

class PhotoAlbum(SQLObject):
    color = StringCol(default='red')
    person = ForeignKey('PersonWithAlbum')

def test_1():
    setupClass([PersonWithAlbum, PhotoAlbum])

    person = PersonWithAlbum(name='Gokou (Kakarouto)')
    assert not person.albumNone # I don't created an album, this way it returns None
    assert isinstance(person.albumInstance, PhotoAlbum)

    album = PhotoAlbum(person=person)
    assert person.albumNone
    assert isinstance(person.albumNone, PhotoAlbum)
    assert isinstance(person.albumInstance, PhotoAlbum)
