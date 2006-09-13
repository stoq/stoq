import unittest

from zope.interface import implements, Interface

from stoqlib.database.exceptions import ProgrammingError
from stoqlib.database.runtime import new_transaction
from stoqlib.domain.base import Domain, ModelAdapter

from tests import base
base # pyflakes


class IDong(Interface):
    pass

class Ding(Domain):
    def __init__(self, connection):
        Domain.__init__(self, connection=connection)
        self.called = False

    def facet_IDong_add(self, **kwargs):
        self.called = True
        adapter_klass = self.getAdapterClass(IDong)
        return adapter_klass(self, **kwargs)

class DingAdaptToDong(ModelAdapter):
    implements(IDong)

Ding.registerFacet(DingAdaptToDong, IDong)

trans = new_transaction()
try:
    Ding.createTable(connection=trans)
    DingAdaptToDong.createTable(connection=trans)
except ProgrammingError:
    pass
else:
    trans.commit()

class FacetTests(unittest.TestCase):
    def setUp(self):
        self.trans = new_transaction()

    def tearDown(self):
        self.trans.close()

    def testAdd(self):
        ding = Ding(connection=self.trans)
        self.assertEqual(IDong(ding, None), None)

        dong = ding.addFacet(IDong, connection=self.trans)
        self.assertEqual(IDong(ding), dong)

    def testAddHook(self):
        ding = Ding(connection=self.trans)
        self.assertEqual(ding.called, False)
        dong = ding.addFacet(IDong, connection=self.trans)
        self.assertEqual(ding.called, True)

    def testGetFacets(self):
        ding = Ding(connection=self.trans)
        self.assertEqual(ding.getFacets(), [])

        facet = ding.addFacet(IDong, connection=self.trans)
        self.assertEqual(ding.getFacets(), [facet])

    def testRegisterAndGetTypes(self):
        class IDang(Interface):
            pass

        class DingAdaptToDang(ModelAdapter):
            implements(IDang)

        try:
            DingAdaptToDang.createTable(connection=self.trans)
        except ProgrammingError:
            pass

        self.assertEqual(Ding.getFacetTypes(), [DingAdaptToDong])

        Ding.registerFacet(DingAdaptToDang, IDang)

        self.failUnless(len(Ding.getFacetTypes()), 2)
        self.failUnless(DingAdaptToDang in Ding.getFacetTypes())
