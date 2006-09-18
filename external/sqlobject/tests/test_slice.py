from sqlobject import *
from sqlobject.tests.dbtest import *

########################################
## Slicing tests
########################################

class Counter(SQLObject):

    number = IntCol(notNull=True)

class TestSlice:

    def setup_method(self, meth):
        setupClass(Counter)
        for i in range(100):
            Counter(number=i)

    def counterEqual(self, counters, value):
        if not supports('limitSelect'):
            return
        assert [c.number for c in counters] == value

    def test_1(self):
        self.counterEqual(
            Counter.select(None, orderBy='number'), range(100))

    def test_2(self):
        self.counterEqual(
            Counter.select(None, orderBy='number')[10:20],
            range(10, 20))

    def test_3(self):
        self.counterEqual(
            Counter.select(None, orderBy='number')[20:30][:5],
            range(20, 25))

    def test_4(self):
        self.counterEqual(
            Counter.select(None, orderBy='number')[:-10],
            range(0, 90))

    def test_5(self):
        self.counterEqual(
            Counter.select(None, orderBy='number', reversed=True),
            range(99, -1, -1))

    def test_6(self):
        self.counterEqual(
            Counter.select(None, orderBy='-number'),
            range(99, -1, -1))
