import unittest

from stoqlib.lib.event import Event


class ReturnStatus:
    pass


class EventTest(unittest.TestCase):

    def _stub_return_wrong_value(self):
        return 1

    def _stub_return_corret_value(self):
        return ReturnStatus()

    def testReturnValueNoConnection(self):
        class MyEvent(Event):
            returnclass = ReturnStatus

        retval = MyEvent.emit()
        self.assertEquals(None, retval)

    def testWrongReturnValue(self):
        class MyEvent(Event):
            returnclass = ReturnStatus

        MyEvent.connect(self._stub_return_wrong_value)
        self.assertRaises(TypeError, MyEvent.emit)

    def testCorrectReturnValue(self):
        class MyEvent(Event):
            returnclass = ReturnStatus

        MyEvent.connect(self._stub_return_corret_value)
        # Shouln't raise
        retval = MyEvent.emit()
        self.assertTrue(isinstance(retval, ReturnStatus))
