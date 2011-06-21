from sqlobject import *
from sqlobject.tests.dbtest import *

deprecated_module()

########################################
## Joins
########################################

class OldPersonJoiner(SQLObject):

    name = StringCol(length=40, alternateID=True)
    _joins = [RelatedJoin('OldAddressJoiner')]

class OldAddressJoiner(SQLObject):

    zip = StringCol(length=5, alternateID=True)
    _joins = [RelatedJoin('OldPersonJoiner')]

class OldImplicitJoiningSO(SQLObject):
    foo = RelatedJoin('Bar')

class OldExplicitJoiningSO(SQLObject):
    _joins = [MultipleJoin('Bar', joinMethodName='foo')]

class TestJoin:

    def setup_method(self, meth):
        setupClass(OldPersonJoiner)
        setupClass(OldAddressJoiner)
        print "CLEARED"
        for n in ['bob', 'tim', 'jane', 'joe', 'fred', 'barb']:
            OldPersonJoiner(name=n)
        for z in ['11111', '22222', '33333', '44444']:
            OldAddressJoiner(zip=z)
        print "INSERTED"

    def test_join(self):
        b = OldPersonJoiner.byName('bob')
        print b
        print b.oldAddressJoiners
        assert b.oldAddressJoiners == []
        z = OldAddressJoiner.byZip('11111')
        b.addOldAddressJoiner(z)
        self.assertZipsEqual(b.oldAddressJoiners, ['11111'])
        self.assertNamesEqual(z.oldPersonJoiners, ['bob'])
        z2 = OldAddressJoiner.byZip('22222')
        b.addOldAddressJoiner(z2)
        self.assertZipsEqual(b.oldAddressJoiners, ['11111', '22222'])
        self.assertNamesEqual(z2.oldPersonJoiners, ['bob'])
        b.removeOldAddressJoiner(z)
        self.assertZipsEqual(b.oldAddressJoiners, ['22222'])
        self.assertNamesEqual(z.oldPersonJoiners, [])

    def assertZipsEqual(self, zips, dest):
        assert [a.zip for a in zips] == dest

    def assertNamesEqual(self, people, dest):
        assert [p.name for p in people] == dest

    def test_joinAttributeWithUnderscores(self):
        # Make sure that the implicit setting of joinMethodName works
        assert hasattr(OldImplicitJoiningSO, 'foo')
        assert not hasattr(OldImplicitJoiningSO, 'bars')

        # And make sure explicit setting also works
        assert hasattr(OldExplicitJoiningSO, 'foo')
        assert not hasattr(OldExplicitJoiningSO, 'bars')

class OldPersonJoiner2(SQLObject):

    name = StringCol('name', length=40, alternateID=True)
    _joins = [MultipleJoin('OldAddressJoiner2')]

class OldAddressJoiner2(SQLObject):

    class sqlmeta:
        defaultOrder = ['-zip', 'plus4']

    zip = StringCol(length=5)
    plus4 = StringCol(length=4, default=None)
    oldPersonJoiner2 = ForeignKey('OldPersonJoiner2')

class TestJoin2:

    def setup_method(self, meth):
        setupClass([OldPersonJoiner2, OldAddressJoiner2])
        p1 = OldPersonJoiner2(name='bob')
        p2 = OldPersonJoiner2(name='sally')
        for z in ['11111', '22222', '33333']:
            a = OldAddressJoiner2(zip=z, oldPersonJoiner2=p1)
            #p1.addOldAddressJoiner2(a)
        OldAddressJoiner2(zip='00000', oldPersonJoiner2=p2)

    def test_basic(self):
        bob = OldPersonJoiner2.byName('bob')
        sally = OldPersonJoiner2.byName('sally')
        assert len(bob.oldAddressJoiner2s) == 3
        assert len(sally.oldAddressJoiner2s) == 1
        bob.oldAddressJoiner2s[0].destroySelf()
        assert len(bob.oldAddressJoiner2s) == 2
        z = bob.oldAddressJoiner2s[0]
        z.zip = 'xxxxx'
        id = z.id
        del z
        z = OldAddressJoiner2.get(id)
        assert z.zip == 'xxxxx'

    def test_defaultOrder(self):
        p1 = OldPersonJoiner2.byName('bob')
        assert ([i.zip for i in p1.oldAddressJoiner2s]
                == ['33333', '22222', '11111'])


teardown_module()
