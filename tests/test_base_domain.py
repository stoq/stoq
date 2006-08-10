import unittest

from zope.interface import implements
from stoqlib.domain.base import ConnInterface, Domain, ModelAdapter
from stoqlib.lib.runtime import new_transaction

from tests import base
base # pyflakes


class IDong(ConnInterface):
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

conn = new_transaction()
Ding.createTable(connection=conn)
DingAdaptToDong.createTable(connection=conn)
conn.commit()

class FacetTests(unittest.TestCase):
    def setUp(self):
        self.conn = new_transaction()

    def tearDown(self):
        self.conn.close()

    def testAdd(self):
        ding = Ding(connection=self.conn)
        self.assertEqual(IDong(ding), None)

        dong = ding.addFacet(IDong, connection=self.conn)
        self.assertEqual(IDong(ding), dong)

    def testAddHook(self):
        ding = Ding(connection=self.conn)
        self.assertEqual(ding.called, False)
        dong = ding.addFacet(IDong, connection=self.conn)
        self.assertEqual(ding.called, True)

    def testGetFacets(self):
        ding = Ding(connection=self.conn)
        self.assertEqual(ding.getFacets(), [])

        facet = ding.addFacet(IDong, connection=self.conn)
        self.assertEqual(ding.getFacets(), [facet])

    def testRegisterAndGetTypes(self):
        class IDang(ConnInterface):
            pass

        class DingAdaptToDang(ModelAdapter):
            implements(IDang)

        DingAdaptToDang.createTable(connection=self.conn)

        self.assertEqual(Ding.getFacetTypes(), [DingAdaptToDong])

        Ding.registerFacet(DingAdaptToDang, IDang)

        self.failUnless(len(Ding.getFacetTypes()), 2)
        self.failUnless(DingAdaptToDang in Ding.getFacetTypes())
